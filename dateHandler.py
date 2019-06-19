import pandas as pd
import re

class DateHandler():
    
    def __init__(self, tokens=None, schema=None):
        
        #Q(): Are we currently able to identify the presence of the date?
            #A(): Year, but it is ambiguous
        self.tokens = tokens
        #TODO(): tie in schema to have sense of how to form sql
        self.schema=schema
        # link vocab to common date cases
        self.vocab = {"getDate":["on [date]", "for [date]",
                                 "of [date]", "where [date]",
                                 "right [date]", "in [date]"
                                ],
                      #ex. of getDate: what is the inventory right now?
                      "getPeriod":["from [date] to [date]", "between [date] and [date]",
                                   "period of [date] to [date]", "in [date] to [date]"
                                  ], 
                      #ex. of getPeriod: what is was our inventory from april to june?
                      "getLastDate":["last [date]", "[date] last year", 
                                     "[date] of last year", "last year's [date]"
                                    ], 
                      #ex. of getLastDate: what was revenue last october?
                      "getLastPeriod":["last [date]", "prior [date]", "previous [date]"], 
                      #ex. of getLastPeriod: what was the budget last year in between october and december?
                      #ex. of getMultiple: can you return the budget for fy quarter 2 and 4 in 2017?
                      "triggers":["january", "february", "march", "april", "may", "june",
                                  "july", "august", "september", "october", "november",
                                  "december", "jan", "feb", "mar", "apr", "jun", "jul",
                                  "aug", "sep", "oct", "nov", "dec", "quarter", "period",
                                  "duration", "year", "month"
                                 ]
                     }
        self.parser.mos = r"(?:[jJ]an*)|(?:[fF]eb*)|(?:[mM]ar*)|(?:[aA]pr*)|(?:[mM]ay*)|(?:[jJ]un*)|(?:[jJ]ul*)|(?:[aA]ug*)|(?:[sS]ep*)|(?:[oO]ct*)|(?:[nN]ov*)|(?:[dD]ec*)"
        self.parser.mmddyys = r"(((\d{2})|(\d{1}))[/.-](\d{2})[/.-]((\d{4})|(\d{2}))$)|(((\d{2})|(\d{1}))[/.-](\d{2})[/.-]((\d{4})|(\d{2}))$)"
        self.parser.mmyys = None
    # is coercible to date? how many x in 2012? what department is employee # 2012 in ?
    
    def identifyDateCase(self, tokens):
        try: 
            self.getPhrases=getPhrases
            self.evalPhrases=evalPhrases
            # eval presence of trigger w/in sentence
            return self.getPhrases().evalPhrases()
        except Exception as e:
            return e
    def getDate(self):
        try:
            date_ents = self.date_ents
            schema = self.schema
            # eval if schema stores date in single date col or multiple cols
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
        try:
            tokens = self.tokens
            if pd.Series(tokens).isin(self.vocab["triggers"]):
                # key: date_ent -> sub-key: phrase, query --> values
                date_ents = dict((k, {}) for k in set(tokens).intersection(set(self.vocab["triggers"])))
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
    