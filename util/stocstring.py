'''Module for dealing with stochastic strings'''
import re
from random import uniform, triangular, betavariate, expovariate, gammavariate, gauss, lognormvariate, normalvariate, vonmisesvariate, paretovariate, weibullvariate, randrange, choice
from distr import RandDist, ChoiceDist, weightedchoice


class StringMacro:
    '''Class that holds macros for StocStrings'''
    def __init__(self, input_string):
        # strip any lingering macro formatting
        if input_string.startswith("!{") and input_string.endswith("}"):
            input_string = input_string[2:-1]
        self._original = input_string

    def execute(self):
        '''evaluate the macro and return the result'''
        # TODO: pass locals / globals dictionary to make this more safe
        return eval(self._original)

    def __str__(self):
        return str(self.execute())

    def __repr__(self):
        return "StringMacro(%s)" % self._original

# TODO: add names to the results of macros to allow them to be named later
class StocString:
    '''Class representing and processsing stochastic strings'''
    # regex that captures the macros
    # this regex cannot work, we need a LR parser to check open / closed parentheses

    def __init__(self, input_string):
        # keeping a copy of the master string
        self.original = input_string

        # parse the string and get list of tokens
        self.tokens = [""]
        depth = 0
        macro_started = False
        prev = None
        for char in input_string:
            self.tokens[-1] += char
            if macro_started:
                if char == "{":
                    depth += 1
                elif char == "}":
                    depth -= 1
                    if depth == 0:
                        macro_started = False
                        self.tokens[-1] = StringMacro(self.tokens[-1])
                        self.tokens.append("")
            elif char == "{" and prev == "!":
                macro_started = True
                # remove the !{ that was added to the previous string
                self.tokens[-1] = self.tokens[-1][:-2]
                self.tokens.append("!{")
                depth += 1
            prev = char

    def __repr__(self):
        output = ""
        for token in self.tokens:
            output += repr(token)
        return output

    def __str__(self):
        output = ""
        for token in self.tokens:
            output += str(token)
        return output

    @staticmethod
    def process(input_string):
        '''Directly process a string in the StocString format
        returns a normal string
        '''
        return str(StocString(input_string))

# TODO: make a CachedStocString that only updates 
# if a certain amount of time has expired or if it is refreshed

'''
Examples:

my_stoc = StocString("Johnny ate !{randrange(1, 10)} apple(s), !{ weightedchoice({'what the heck':1, 'wow': 50}) }! what a !{choice(['fella', 'guy'])}")
total = 0
for i in range(10):
    print(my_stoc)

Result:
Johnny ate 5 apple(s), wow! what a fella
Johnny ate 2 apple(s), wow! what a guy
Johnny ate 5 apple(s), wow! what a guy
Johnny ate 4 apple(s), wow! what a fella
Johnny ate 3 apple(s), wow! what a fella
Johnny ate 7 apple(s), what the heck! what a fella
Johnny ate 8 apple(s), wow! what a guy
Johnny ate 1 apple(s), wow! what a fella
Johnny ate 5 apple(s), wow! what a fella
Johnny ate 7 apple(s), wow! what a guy
'''
