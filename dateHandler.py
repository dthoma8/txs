import pandas as pd
import re
import  joblib

class DateHandler():
    
    def __init__(self, tokens=None, schema=None):
        
        #Q(): Are we currently able to identify the presence of the date?
            #A(): Year, but it is ambiguous
        self.tokens = tokens
        
        self.schema=schema#TODO(): tie in schema to have sense of how to form sql
        
        self.vocab = {"getDate":["on [date]", "for [date]",# link vocab to common date cases, #ex. of getDate: what is the inventory right now?
                                 "of [date]", "where [date]",
                                 "right [date]", "in [date]"
                                ],
                      
                      "getPeriod":["from [date] to [date]", "between [date] and [date]",#ex. of getPeriod: what is was our inventory from april to june?
                                   "period of [date] to [date]", "in [date] to [date]"
                                  ], 
                      
                      "getLastDate":["last [date]", "[date] last year", #ex. of getLastDate: what was revenue last october?
                                     "[date] of last year", "last year's [date]"
                                    ], 
                      
                      "getLastPeriod":["last [date]", "prior [date]", "previous [date]"], #ex. of getLastPeriod: what was the budget last year in between october and december?
                      
                      "triggers":["january", "february", "march", "april", "may", "june", #ex. of getMultiple: can you return the budget for fy quarter 2 and 4 in 2017?
                                  "july", "august", "september", "october", "november",
                                  "december", "jan", "feb", "mar", "apr", "jun", "jul",
                                  "aug", "sep", "oct", "nov", "dec", "quarter", "period",
                                  "duration", "year", "month"
                                 ]
                     }
        self.parser_dict = {
            "month":r"(?:[jJ]an*)|(?:[fF]eb*)|(?:[mM]ar*)|(?:[aA]pr*)|(?:[mM]ay*)|(?:[jJ]un*)|(?:[jJ]ul*)|(?:[aA]ug*)|(?:[sS]ep*)|(?:[oO]ct*)|(?:[nN]ov*)|(?:[dD]ec*)",
            "date":{"mmddyys":r"(((\d{2})|(\d{1}))[/.-](\d{2})[/.-]((\d{4})|(\d{2}))$)|(((\d{2})|(\d{1}))[/.-](\d{2})[/.-]((\d{4})|(\d{2}))$)",
                    "mmyys":None,
            },
            "duration":None,
            "period":None,#TODO(): find the diff ways can be ref'd
            "quarter":None#TODO(): find the diff ways can be ref'd
        }
    # is coercible to date? how many x in 2012? what department is employee # 2012 in ?
    def getDate(self, idx):
        try:
            # assumes one case - spc'd by idx
            date_ent = self.date_ents[idx]

            # eval if schema stores date in single date col or multiple cols
            # if month, day, year in schema or date, if quarter or other period stored
            self.schema.evalDateSchema()

            pass
        except Exception as e:
            return 
    def getPeriod(self):
        try:
            date_ents = self.date_ents
            schema = self.schema
            pass
        except Exception as e:
            return e
    def getLastDate(self):
        try:
            date_ents = self.date_ents
            schema = self.schema
            pass
        except Exception as e:
            return e
    def getLastPeriod(self):
        try:
            date_ents = self.date_ents
            schema = self.schema
            pass
        except Exception as e:
            return e
    def getPhrases(self):    
        print("getPhrases called")
        try:
            tokens = self.tokens
            print("tokens avail", tokens)
            if any(pd.Series(tokens).isin(self.vocab["triggers"])):
                print("id'd tokens that are also date triggers")
                # key: date_ent -> sub-key: phrase, query --> values
                date_ents = dict((k, {}) for k in set(tokens).intersection(set(self.vocab["triggers"])))
                print("formed date entities: ", date_ents)
                for date_ent in date_ents:
                    #initialize lists
                    date_ents[date_ent]["phrase"], date_ents[date_ent]["query"], date_ents[date_ent]["case"] = [], [], []
                    idx = tokens.index(date_ent)
                    # construct possible phrases
                    date_ents[date_ent]["phrase"].extend([tokens[idx-2]+tokens[idx-1]+"[date]", "[date]"+tokens[idx+1]+tokens[idx+2]])
                # add attribute
                self.date_ents = date_ents
                return self
            else:
                return("No Date Present")
        except Exception as e:
            return e
        
    def evalPhrases(self):
        try:
            match=None
            # for equivalency(?) between the constructs id'd and the user usage
            # if the user usage is in any of our focus areas then we can proceed to implement the func
            # rel to the focus area
            # if there are multiple occurences of the date entities, this will need to occur
            # @ each enity.
            # end goal: construct a sql query to plug in elsewhere
            for date_ent in self.date_ents:
                phrases = self.date_ents[date_ent]["phrase"]
                for case in self.vocab:
                    terms=self.vocab[case]
                    matches = crossCheck(terms).check(phrases)
                    if matches:
                        self.date_ents[date_ent][phrase] = matches
                        self.date_ents[date_ent]["case"]=case
                        break
            return self
        except Exception as e:
            return e
    class crossCheck(list):
        def check(self, other_list):
            try:
                for st in self:
                    for ot in other_list:
                        matches = list(filter(lambda : v != "", re.findall(st, ot)))
                        return matches
            except Exception as e:
                return e
        def parserCheck(self):
            pass


    def identifyDateCase(self, tokens):
        try: 
            
            self.tokens=tokens
            # eval presence of trigger w/in sentence
            self=self.getPhrases().evalPhrases()
            return self
        except Exception as e:
            return e

    def evalDateSchema(self):
        
        try:
            # peak out how schema is currently stored
            entities, tables = joblib.open("curschema.pkl")
            matches = set([k.lower() for k in entities.keys()]).intersection(self.vocab["triggers"])
            # so now we have identified matches from trigger words to the schema. meaning, each of the 
            #trigger words that align with the schema are columns in the dataset that we will have to 
            # use to query. at this point it makes sense to hava a parser associated with each possible 
            # combination and parse according to this using our dictionary of parsers
            if matches:
                #proceed
                if "date" in matches:
                    pass
                elif "year" in matches:
                    pass
            else:
                pass
            return scheme
        except Exception as e:
            return e
    # got this from a little duckling: https://github.com/facebook/duckling/tree/master/Duckling
    def MMDDRule(self, date_ent):
        pass
    def MMDDYYYYRule(self, date_ent):
        pass
    def quarterTimeRule(self, date_ent):
        pass
    def halfTimeRule(self, date_ent):
        pass
    def fortnightRule(self, date_ent):
        pass
    # pipeline
    # va funcs
    # schema gets passed to the js file
    # output formatting
    # visualization
    # dropdown
    