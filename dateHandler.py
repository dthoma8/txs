import pandas as pd
import re
import joblib
from datetime import datetime 
class DateHandler():
    def __init__(self, tokens=None, schema=None):
        # Q(): Are we currently able to identify the presence of the date?
            # A(): Year, but it is ambiguous
        self.tokens = tokens
        self.schema = {"entities":["repair_date", "equip_name", "model_num"]}#{"entities": ["col1", "col2", "month", "day", "year", "col3"]}{"entities":["maint_month", "maint_year", "maint_day"]}  # TODO(): tie in schema.pkl
        self.schema_curr_style = None
        self.schema_style = {
            "sep_cols": ["[mM][oO][nN]([tT][hH])?", "[yY][eE][aA][rR]", "[dD][aA][yY]",
                         # fy starts oct1
                         "([qQ]([uU][aA][rR][tT][eE][rR])?|([tT][rR])?)", "([fF]([iI][sS][cC][aA][lL])?[yY]([eE][aA][rR])?)"
                         ],
            "one_col": ["[dD][aA][tT][eE]"]# consider other naming conventions
        }
        self.vocab_triggers = {
            "triggers": ["[jJ]an(uary)?", "[fF]eb(ruary)?", "[mM]ar(ch)?", "[aA]pr(il)?", "[mM]ay", "[jJ]un(e)?", #ex. of getMultiple: can you return the budget for fy quarter 2 and 4 in 2017?
                         "[jJ]ul(y)?", "[aA]ug(ust)?", "[sS]ep(tember)?", "[oO]ct(ober)?", "[nN]ov(ember)?",
                         "[dD]ec(ember)?","[qA]uarter", "[pP]eriod",
                         "[dD]uration", "[yY]ear", "[mM]o(nth)?", "[dD]ay", "[dD]ate", "[fF](iscal)?[yY](ear)?",
                         "[wW]eek", "(?: [sS]un*)|(?: [mM]on*)|(?: [tT]ues*)|(?: [wW]ednes*)|(?: [tT]hurs*)|(?: [fF]ri*)|(?: [sS]atur*)"
                        ]
        }
        self.vocab_cases = {
            "getLastDate": ["((?:[lL]ast)|(?:[pP]rior)|(?:[bB]efore)|(?:[pP]revious)|(?:[pP]rior))*"],  # ex. of getLastPeriod: what was the budget last year in between october and december?
            "getPeriod": ["[fFrRoOmM]*(.)*[tToO]*(.)", "[bBeEtTwWeEeEnN]*(.)*([aAnNdD])?*(.)*",  # ex. of getPeriod: what is was our inventory from april to june?
                          "[pPeErRiIoOdD]*([oOfF])?*(.)*[tToO]*(.)*", "[iInN]*(.)*[tToO]*(.)*"
                          ],
            "getDate": ["[oOnN]* (.)", "[fFoOrR]* (.)",  # link vocab to common date cases, #ex. of getDate: what is the inventory right now?
                        "[oOfF]* (.)", "[wWhHeErReE]* (.)",
                        "[rRiIgGhHtT] (.)", "[iInN]* (.)"
                        ],   
        }
        self.parser_dict = {
            "month": "(?:[jJ]an*)|(?:[fF]eb*)|(?:[mM]ar*)|(?:[aA]pr*)|(?:[mM]ay*)|(?:[jJ]un*)|(?:[jJ]ul*)|(?:[aA]ug*)|(?:[sS]ep*)|(?:[oO]ct*)|(?:[nN]ov*)|(?:[dD]ec*)",
            "mmddyys": r"(((\d{2})|(\d{1}))[/.-](\d{2})[/.-]((\d{4})|(\d{2}))$)|(((\d{2})|(\d{1}))[/.-](\d{2})[/.-]((\d{4})|(\d{2}))$)",
            #"mmyys": None,
            "year_num": r"(\d{4})",
            "week":"[wW]eek",
            "duration": "None",
            #"period": None,  # TODO(): find the diff ways can be ref'd
            #"quarter": None  # TODO(): find the diff ways can be ref'd
        }
        self.month_maps = {"january":1, "february":2, "march":3, "april":4, "may":5, 
                           "june":6, "july":7, "august":8, "september":9, "october":10,
                           "november":11, "december":12, "jan":1, "feb":2, "mar":3, "apr":4, 
                           "jun":6, "jul":7, "aug":8, "sep":9, "oct":10, "nov":11, "dec":12
                          }
    class listFuncs(list):
        def walkLeft(self, idx=0, dist=0):
            #print("walkLeft called\n")
            space = self[:idx]
            #print("this is space: ", space)
            if space != []:
                if dist > len(space):
                    dist = dist-len(space)
                    ##print("new dist", dist)
                tokens_along_walk=[]
                if dist == 0:
                    return tokens_along_walk
                else:
                    new_idx = idx
                    for i in range(dist):
                        if new_idx >= 0:
                            new_idx -= 1
                            ##print("this is the new index", new_idx)
                            ##print("so this is the term that should be returned", space[new_idx])
                            tokens_along_walk.append(space[new_idx])
                        else:
                            break

                if len(tokens_along_walk) > 1:
                    tokens_along_walk.reverse()
                    phrase = [" ".join(tokens_along_walk)+" "+self[idx]]
                else:
                    phrase = [tokens_along_walk[0]+" "+self[idx]]
                #print("this is the phrase from walking left", phrase)
                return phrase
            else:
                return []
        def walkRight(self, idx=0, dist=0):
            #print("walkRight called\n")
            if idx == 0:
                space = self
                #print("nochanges", space)
            else:
                space = self[idx+1:]  # bottomisinclusive
                #print("changes", space)
            if space != []:
                #print("contents present")
                #there is space
                horizon = len(space)
                # calculate available space to walk to horizon
                if dist > dist-((idx+dist)-horizon):
                    #print("redefining distance")
                    dist = dist-((idx+dist)-horizon)
                    ##print("this is the new distance to walk", dist)
                tokens_along_walk = []
                if dist == 0:
                    return tokens_along_walk
                else:
                    for i in range(dist):
                        tokens_along_walk.append(space[i])
                phrase = [self[idx]+" "+" ".join(tokens_along_walk)]
                #print("phrase returned from walking right", phrase)
                
                return phrase
            else:
                return []
    def getDateEnts(self, date_token=None):
        print("getDateEnts called")
        try:
            tokens = self.tokens
            trigids = [re.search("|".join(self.vocab_triggers["triggers"]), t) for t in tokens]
            if any(trigids):
                idxs = pd.Series(trigids).dropna().index.tolist()
                # key: date_ent -> sub-key: phrase, query --> values
                date_ents = dict((k.group(), {}) for k in trigids if k)
                for i, date_ent in enumerate(date_ents):
                    idx = idxs[i]
                    date_ents[date_ent]["date_type"], date_ents[date_ent]["phrase"], date_ents[date_ent]["case"], date_ents[date_ent]["value"] = [], [], [], [] # initialize lists
                    date_ents[date_ent]["phrase"].extend(self.listFuncs(tokens).walkLeft(idx=idx, dist=2)+self.listFuncs(tokens).walkRight(idx=idx, dist=2))  # construct possible phrases    
                    [date_ents[date_ent]["date_type"].append(date_type) for date_type in self.parser_dict if re.search(self.parser_dict[date_type], date_ent) and date_ents[date_ent]["date_type"]==[]]

                #print("these are the date entities: ", date_ents)
                self.date_ents = date_ents  # add attribute
                #print("this is the outgoing self", self)
                return self
            else:
                mxs = [re.search(self.parser_dict["mmddyys"],t.replace("?", "")) for t in tokens]
                #print("parser object", self.parser_dict["mmddyys"])
                if not any(mxs):
                    return("No Date Present")
                else:
                    date_ents = dict((k.group(), {}) for k in mxs if k)
                    idxs = pd.Series(mxs).dropna().index.tolist()
                    for i, date_ent in enumerate(date_ents):
                        date_ents[date_ent]["date_type"], date_ents[date_ent]["phrase"], date_ents[date_ent]["case"], date_ents[date_ent]["value"] = [], [], [], [] # initialize lists
                        idx = idxs[i]
                        date_ents[date_ent]["phrase"].extend(self.listFuncs(tokens).walkLeft(idx=idx, dist=2)+self.listFuncs(tokens).walkRight(idx=idx, dist=2))  # construct possible phrases
                        [date_ents[date_ent]["date_type"].append(date_type) for date_type in self.parser_dict if re.search(self.parser_dict[date_type], date_ent)]

                    #print("these are the date entities: ", date_ents)
                    self.date_ents = date_ents  # add attribute
                    #print("this is the outgoing self", self)
                    return self
        except Exception as e:
            return e
    def idDateCase(self):
        print("identifyDateCase called")
        try:
            #print("this is the upcoming self", self)
            # runs after getDateEnts
            if hasattr(self, "date_ents"):
                for date_ent in self.date_ents:
                    for case in self.vocab_cases:
                        #print("this is the active case beign assessed",case)
                        case_string = "|".join(self.vocab_cases[case])
                        if any([re.search(case_string, p) for p in self.date_ents[date_ent]["phrase"]]):
                            self.date_ents[date_ent]["phrase"] = [re.search(case_string, p) for p in self.date_ents[date_ent]["phrase"]][0].string
                            #print("this is the phrase", self.date_ents[date_ent]["phrase"])
                            self.date_ents[date_ent]["case"] = case
                            #print("this is the case:", self.date_ents[date_ent]["case"])
                            break
                return self
            else:
                return("Error! shouldve run getDateEnts first.")
        except Exception as e:
            return e
    def inferSchema(self):
        print("inferSchema called")
        try:
            schema = self.schema
            #print("this is what your schema looks like: ", schema)
            for style in self.schema_style:
                style_string = "|".join(self.schema_style[style])
                if any([re.search(style_string,e).group() for e in self.schema["entities"] if re.search(style_string, e) is not None]):
                    self.schema_curr_style=style
                    [re.search(style_string, e) for e in self.schema["entities"] if re.search(style_string, e) is not None][0].string
                    break
            return self
        except Exception as e:
            return e
    def getLast(self, entity_name, entity_obj):
        print("getLast called")
        
        try:
            now = datetime.now()
            date_type = entity_obj["date_type"][0]            
            if date_type == 'year':
                last_year = now.year-1
                self.date_ents[entity_name]["value"]={"year":last_year}
                print("last value", {"year":last_year})
                return self
            elif date_type == "month":
                # two lanes, there is a month id'd or it is generically referencing last month
                if entity_name == "month":
                    last_month = now.month-1
                    rev_month_maps = dict((v,k) for k,v in self.month_maps.items())
                    last_month = rev_month_maps[last_month]
                    self.date_ents[entity_name]["value"]={"month":last_month}
                    print("last value", {"month":last_month})
                    return self
                else:
                    last_year = now.year-1
                    self.date_ents[entity_name]["value"]={"month":entity_name, "year":last_year}
                    print("last value", {"month":entity_name, "year":last_year})
                    return self
            elif date_type == "week":
                pass
            elif date_type == "day":
                pass
            elif date_type == "fiscal_year":
                pass
            elif date_type == "quarter":
                pass
            return self
        except Exception as e:
            return e
    def getRange(self):
        print("getRange called")
        pass
    def reformatDateEntities(self):
        print("reformatDateEntities called")
        try:
            for date_ent in self.date_ents:
                # need to check if prior year provided
                if self.schema_curr_style == "one_col":
                    print("in one_col condition")
                    if re.search(self.parser_dict["mmddyys"], date_ent):#iftheyveprovidedadatedonothing
                        print("no reformatting needed for one_col")
                        return self
                    else:
                        print("reformatting one_col")# give me all transactions in 2012, give me all transactions in october, give me all transactions in october 2012, give me all transactions on christmas for the last 6 years    
                        if date_ent in self.month_maps:
                            new_date_ent = self.month_maps[date_ent]
                            #print("this is the new date_ent", new_date_ent)
                            #print("this is the current date_ent", self.date_ents[date_ent])
                            if self.date_ents[date_ent]["case"] == "getLastDate":
                                self.getLast(date_ent, self.date_ents[date_ent])

                        if "year" in self.date_ents[date_ent]["value"]:
                            print("are we getting here?")
                            #date_ent = {"date":str(new_date_ent)+"/01/"+str(self.date_ents[date_ent]["year"])}
                            print({"value":str(new_date_ent)+"/01/"+str(self.date_ents[date_ent]["year"])})
                            return self
                        else:
                            curr_year = datetime.now().year
                            #self.date_ents[date_ent]={"date":str(date_ent)+"/01/"+str(curr_year)}
                            print({"value":str(new_date_ent)+"/01/"+str(curr_year)})
                            return self
                elif self.schema_curr_style == "sep_cols":
                    print("in sep_cols condition")
                    if re.search(self.parser_dict["mmddyys"], date_ent):
                        print("reformatting happening for sep_cols")
                        month, day, year = date_ent.split("/").split("-").split(".")#TODO():obvfindsomethingbetter | operator potentially
                        rev_month_maps = dict((v, k) for k,v in self.month_maps.items())
                        self.date_ents[date_ent]["value"]={"month":rev_month_maps[month], "day":day, "year":year}
                        return self
                    else:
                        print("no reformatting needed for sep_cols")
                        #self.date_ents[date_ent]["value"]=date_ent
                        return self
                else:
                    return "Oh No! Style may not be defined"#consider other cases that may be applicable
        except Exception as e:
            return e
    def run(self):
        #print("call made")
        #print("this is the incoming obj", dir(self))
        try:
            self = self.getDateEnts() # get date tokens and ngrams
            print("this is what you've done. fix it: ", self)
            self = self.idDateCase() # use date ngrams to relay usage from user to a case
            print("this is what you've done. fix it: ", self)
            self = self.inferSchema() # view what format the dates need to be normalized to from user usage
            print("this is what you've done. fix it: ", self)
            self.reformatDateEntities() # normalize the user input dates to allowable date construction given schema
            #print("this is what you've done. fix it: ", self)
            return self
        except Exception as e:
            return e
