import fileinput
import json
from pyparsing import (
    Forward,
    Group,
    Suppress,
    Word,
    alphanums,
    delimitedList,
    quotedString,
    originalTextFor,
    nestedExpr,
    SkipTo,
    Literal,
    removeQuotes,
    LineStart,
    Optional,
)


class JenkinsFileParser:

    STAGE_KEY = 'stage'
    COMMENTED_STAGE_KEY = 'commented_stage'

    def __init__(self, filename='Jenkinsfile'):
        self.filename = filename
        self.create_grammar()

    def create_grammar(self):
        self.beg = SkipTo(LineStart() + Literal('/*')*(0, 1) + Literal('stage'), ignore=Literal('stages'))
        self.block = Forward()
        self.parallel = Suppress('parallel') + self.nested(self.block)
        self.parallel.setParseAction(lambda t: t[0])
        self.environment = Suppress('environment') + self.nested()
        self.stage_content = (
            self.nested((self.parallel | self.environment.suppress()), 'parallel') |
            self.nested().suppress()
        )

        self.stage = Group(
            Suppress('stage' + '(') +
            quotedString('stage_name').setParseAction(removeQuotes) +
            Suppress(')') +
            self.stage_content)(
                self.STAGE_KEY + '*'
            )
        self.commented_stage = Group(Suppress('/*') + self.stage + Suppress('*/'))(self.COMMENTED_STAGE_KEY + '*')
        self.any_stage = self.stage | self.commented_stage
        self.block << Group(self.parallel | self.any_stage)('block*')

    @staticmethod
    def nested(elem=None, name=None):
        expr = nestedExpr('{', '}', content=elem, ignoreExpr=Literal('*/'))
        if name:
            return expr.setResultsName(name)
        return expr

    def evaluate_stages(self):
        a = self.beg.suppress() + self.block[...]
        test = a.parseFile(self.filename)
        #  print(test.asDict())
        #  print(json.dumps(test.asDict(), indent=4))
        return test.asDict()

    def find_stage_by_name(self, name, content):
        quoted_name = (Literal('"') | Literal("'")).suppress() + name + (Literal('"') | Literal("'")).suppress()
        #  named_stage = Literal('/*')*(0, 1) + 'stage' + '(' + quoted_name + ')' + self.nested() + Literal('*/')*(0, 1)
        named_stage = 'stage' + '(' + quoted_name + ')' + self.nested()
        commented_named_stage = Literal('/*') + 'stage' + '(' + quoted_name + ')' + self.nested() + Literal('*/')
        return next((named_stage | commented_named_stage).scanString(content))


def definitions():
    expression = Forward()
    array = Suppress('[') + delimitedList(expression) + Suppress(']')
    expression << (quotedString | array)('val')

    ident = Word(alphanums + '_')('var')
    definition = Group(Suppress('def') + ident + Suppress('=') + expression)("def*")
    program = definition[...]

    test = program.parseFile('tmp')

    #  print(originalTextFor(program))
    print(test.asDict())

if __name__ == "__main__":
    p = JenkinsFileParser()
    p.evaluate_stages()
