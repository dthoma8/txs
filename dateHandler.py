import pandas as pd
import re
import joblib
from datetime import datetime 

q = "how much was revenue last october?"

class DateHandler():
    def __init__(self, tokens=None, schema=None):
        # Q(): Are we currently able to identify the presence of the date?
            # A(): Year, but it is ambiguous
        self.tokens = tokens
        self.schema = {"entities":["repair_date", "equip_name", "model_num"]}#{"entities": ["col1", "col2", "month", "day", "year", "col3"]}  # TODO(): tie in schema.pkl
        self.schema_curr_style = None
        self.schema_style = {
            "sep_cols": ["[mM][oO][nN]([tT][hH])?", "[yY][eE][aA][rR]", "[dD][aA][yY]",
                         # fy starts oct1
                         "[qQ]([uU][aA][rR][tT][eE][rR])?|([tT][rR])?", "[fF]([iI][sS][cC][aA][lL])?[yY]([eE][aA][rR])?"
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
            "month": r"(?:[jJ]an*)|(?:[fF]eb*)|(?:[mM]ar*)|(?:[aA]pr*)|(?:[mM]ay*)|(?:[jJ]un*)|(?:[jJ]ul*)|(?:[aA]ug*)|(?:[sS]ep*)|(?:[oO]ct*)|(?:[nN]ov*)|(?:[dD]ec*)",
            "date": {"mmddyys": r"(((\d{2})|(\d{1}))[/.-](\d{2})[/.-]((\d{4})|(\d{2}))$)|(((\d{2})|(\d{1}))[/.-](\d{2})[/.-]((\d{4})|(\d{2}))$)",
                     "mmyys": None,
                     },
            "year": ["[yY]ear", r"(\d{4})"],
            "week":"[wW]eek",
            "duration": None,
            "period": None,  # TODO(): find the diff ways can be ref'd
            "quarter": None  # TODO(): find the diff ways can be ref'd
        }
        self.month_maps = {1:"january", 2: "february", 3: "march", 4:"april", 5:"may", 6:"june", 7:"july", 8:"august", 9:"september", 10:"october", 11:"november", 12:"december", "jan":"january", "feb":"feburary", "mar":"march", "apr":"april", "jun":"june", "jul":"july", "aug":"august", "sep":"september", "oct":"october", "nov":"november", "dec":"december"}
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
    # is coercible to date? how many x in 2012? what department is employee # 2012 in ?
    def getDateEnts(self, date_token=None):
        print("getDateEnts called")
        try:
            tokens = self.tokens
            trigids = [re.search("|".join(self.vocab_triggers["triggers"]), t) for t in tokens]
            print("tokens id'd")
            if any(trigids):
                idxs = pd.Series(trigids).dropna().index.tolist()
                # key: date_ent -> sub-key: phrase, query --> values
                date_ents = dict((k.group(), {}) for k in trigids if k)
                for i, date_ent in enumerate(date_ents):
                    idx = idxs[i]
                    date_ents[date_ent]["phrase"], date_ents[date_ent]["case"], date_ents[date_ent]["key"], date_ents[date_ent]["value"] = [], [], [], []  # initialize lists
                    date_ents[date_ent]["phrase"].extend(self.listFuncs(tokens).walkLeft(idx=idx, dist=2)+self.listFuncs(tokens).walkRight(idx=idx, dist=2))  # construct possible phrases

                #print("these are the date entities: ", date_ents)
                self.date_ents = date_ents  # add attribute
                return self
            else:
                mxs = [re.search(self.parser_dict["date"]["mmddyys"],t.replace("?", "")) for t in tokens]
                #prin,t("parser object", self.parser_dict["date"]["mmddyys"])
                #print('these are the tokens being passed in ', tokens)
                if not any(mxs):
                    #print("imhere2")
                    return("No Date Present")
                else:
                    #print("imhere3")
                    date_ents = dict((k.group(), {}) for k in mxs if k)
                    idxs = pd.Series(mxs).dropna().index.tolist()
                    for i, date_ent in enumerate(date_ents):
                        date_ents[date_ent]["phrase"], date_ents[date_ent]["case"], date_ents[date_ent]["key"], date_ents[date_ent]["value"] = [], [], [], []  # initialize lists
                        idx = idxs[i]
                        date_ents[date_ent]["phrase"].extend(self.listFuncs(tokens).walkLeft(idx=idx, dist=2)+self.listFuncs(tokens).walkRight(idx=idx, dist=2))  # construct possible phrases
                    #print("these are the date entities: ", date_ents)
                    self.date_ents = date_ents  # add attribute
                    return self
        except Exception as e:
            return e
    def idDateCase(self):
        print("identifyDateCase called")
        try:
            print("this is the incoming obj", self)
            # runs after getDateEnts
            if hasattr(self, "date_ents"):
                print("found attr")
                for date_ent in self.date_ents:
                    print("wemadeit")
                    for case in self.vocab_cases:
                        print("this is the active case beign assessed",case)
                        case_string = "|".join(self.vocab_cases[case])
                        
                        if any([re.search(case_string, p) for p in self.date_ents[date_ent]["phrase"]]):
                            self.date_ents[date_ent]["phrase"] = [re.search(case_string, p) for p in self.date_ents[date_ent]["phrase"]][0].string
                            print("this is the phrase", self.date_ents[date_ent]["phrase"])
                            self.date_ents[date_ent]["case"] = case
                            print("this is the case:", self.date_ents[date_ent]["case"])
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
            schema = ",".join(schema["entities"])#wishlist
            for style in self.schema_style:
                if re.search("|".join(self.schema_style[style]), schema):
                    self.schema_curr_style=style
                    break
            return self
        except Exception as e:
            return e
    def reformatDateEntities(self):
        try:
            for date_ent in self.date_ents:
                # need to check if prior year provided
                if self.schema_curr_style == "one_col":
                    if re.search("|".join(self.parser_dict["mmddyy"]), date_ent):
                        return date_ent
                    else:
                        rev_month_map = dict((v,k) for k,v in self.month_maps.items())
                        if date_ent in rev_month_map:
                            date_ent = rev_month_map[date_ent]
                            print("this is the new date_ent", date_ent)
                        elif date_ent in self.month_maps:
                            date_ent = rev_month_map[self.month_maps[date_ent]]
                            print("this is the new date_ent", date_ent)
                        if "year" in self.date_ents[date_ent]["value"]:
                            #date_ent = {"date":str(date_ent)+"/01/"+str(self.date_ents[date_ent]["year"])}
                            print({"value":str(date_ent)+"/01/"+str(self.date_ents[date_ent]["year"])})
                        else:
                            curr_year = datetime.now().year
                            #self.date_ents[date_ent]={"date":str(date_ent)+"/01/"+str(curr_year)}
                            print({"value":str(date_ent)+"/01/"+str(curr_year)})
                elif self.schema_curr_style == "sep_cols":
                    if re.search("|".join(self.parser_dict["mmddyys"]), date_ent):
                        month, day, year = date_ent.split("/").split("-").split(".")#TODO():obvfindsomethingbetter | operator potentially
                        self.date_ents[date_ent]={"month":self.month_maps[month], "day":day, "year":year}
                    else:
                        return date_ent
                else:
                    return "Oh No! Style may not be defined"#consider other cases that may be applicable
        except Exception as e:
            return e
    class dateFuncs():
        def getLast(self, entity):
            try:
                now = datetime.now()
                date_type = [k for k in entity.keys()][0]
                if date_type == 'year':
                    last_year = now.year-1
                    self.date_ents[entity]["value"]={"year":last_year}
                elif date_type == "month":
                    # two lanes, there is a month id'd or it is generically referencing last month
                    if entity["month"] == "month":
                        last_month = now.month-1
                        last_month = self.month_maps[last_month]
                        self.date_ents[entity]["value"]={"month":last_month}
                    else:
                        last_year = now.year-1
                        self.date_ents[entity]["value"]={"month":entity[date_type], "year":last_year}
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
            pass
    def run(self):
        #print("call made")
        #print("this is the incoming obj", dir(self))
        try:
            self = self.getDateEnts()
            #print("this is the modified obj", dir(self))
            self = self.idDateCase()
            #print("this is the step 2 obj", dir(self))
            self = self.inferSchema()
            #self.reformatDateEntities()
            return self
        except Exception as e:
            return e
