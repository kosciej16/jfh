import attr

from jenkinsfile.jf_parser import JenkinsFileParser


@attr.s(hash=True)
class Stage:
    name = attr.ib()
    is_commented = attr.ib()
    children = attr.ib(factory=list)
    id = attr.ib(default='-1')
    parent = attr.ib(default=None)

    def add_child(self, stage):
        stage.parent = self
        stage.id = f'{self.id}.{len(self.children)+1}'
        if self.is_commented:
            stage.is_commented = True
        self.children.append(stage)

    def update_status(self):
        old_status = self.is_commented
        if all([s.is_commented for s in self.children]):
            self.is_commented = True
        else:
            self.is_commented = False
        return old_status != self.is_commented

    def change_state(self):
        self.is_commented = not self.is_commented
        for child in self.children:
            child.is_commented = self.is_commented
        if self.parent:
            return self.parent.update_status()
        return False

    @property
    def siblings(self):
        if self.parent:
            return self.parent.children
        return []

    def pretty_print(self, prefix=''):
        comm_begin = '/* ' if self.is_commented else ''
        comm_end = ' */' if self.is_commented else ''
        print(f'{prefix}{self.id}:  {comm_begin}{self.name}{comm_end}')
        for n, child in enumerate(self.children, 1):
            child.pretty_print(prefix + '--  ')


class StageTracker:

    STAGE_IDENTIFIER = 1

    def __init__(self, parser: JenkinsFileParser):
        self.parser = parser
        self.stages = {}
        self.mapping = {}
        self.get_stages()

    def get_stages(self):
        raw_stages = self.parser.evaluate_stages()
        self.get_stages_recursively(raw_stages)

    def map_stages(self, parent_identifier):
        for identifier, name in enumerate(self.stages.keys(), 1):
            self.stage_mapping[f'{parent_identifier}.{identifier}'] = name

    def get_stages_recursively(self, stages_subdict, parent_stage=None):
        for raw_stage in stages_subdict.get('block', []):
            is_commented = False
            if 'commented_stage' in raw_stage:
                raw_stage = raw_stage.get('commented_stage')[0]
                is_commented = True
            raw_stage = raw_stage.get('stage')[0]
            stage = self.parse_raw_stage(raw_stage, is_commented, is_root_stage=parent_stage is None)
            if parent_stage:
                parent_stage.add_child(stage)
            else:
                self.stages[stage.name] = stage
            self.mapping[stage.id] = stage

    def parse_raw_stage(self, stage_as_dict, is_commented, is_root_stage=False):
        name = stage_as_dict.get('stage_name')
        nested = stage_as_dict.get('parallel')
        result = Stage(name, is_commented)
        if is_root_stage:
            result.id = str(self.STAGE_IDENTIFIER)
            self.STAGE_IDENTIFIER += 1
        if nested:
            self.get_stages_recursively(nested[0], result)

        return result

    def is_commented(self, stage_name):
        if stage_name not in self.stages:
            return False
        return self.stages.get(stage_name).is_commented

    def get_parent(self, stage_name):
        return self.stages.get(stage_name).parent

    def get_stage(self, stage_id):
        return self.mapping.get(stage_id)

    def print_stages(self):
        for stage in self.stages.values():
            stage.pretty_print()
            print()
