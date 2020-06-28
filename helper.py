from jenkinsfile.jf_parser import JenkinsFileParser

from jenkinsfile.stage_tracker import StageTracker


class JenkinsFileHelper:
    def __init__(self, parser):
        self.parser = parser
        self.filename = parser.filename
        self.stage_tracker = StageTracker(parser)

    def process_stage_by_id(self, stage_id):
        self.process_stage(self.stage_tracker.get_stage(stage_id))

    def process_stage(self, stage, switch_state=True):
        with open(self.filename, 'r+') as f:
            content = f.read()
            scan_result = self.parser.find_stage_by_name(stage.name, content)
            if not scan_result:
                return
            res = ''
            parent_state_changed = switch_state and stage.change_state()
            if stage.is_commented:
                # changing state of stage updated parent
                if parent_state_changed:
                    self.process_stage(stage.parent, switch_state=False)
                    return
                res = self.comment(content, scan_result)
                res = res[0:2] + self.uncomment(res[2:-2], scan_result) + res[-2:]
            else:
                if parent_state_changed:
                    self.process_stage(stage.parent, switch_state=False)
                    for child in stage.siblings:
                        if child.name != stage.name:
                            self.process_stage(child, switch_state=False)
                    return
                res = self.uncomment(content, scan_result)
            f.seek(0)
            f.write(res)
            f.truncate()

    def comment(self, content, scan_result):
        tmp = self.put_inside_string(content, scan_result[2], ' */')
        return self.put_inside_string(tmp, scan_result[1], '/* ')

    def uncomment(self, content, scan_result):
        subcontent = content[scan_result[1] : scan_result[2]]
        return content.replace(subcontent, subcontent.replace('/* ', '').replace(' */', ''))

    @staticmethod
    def put_inside_string(string, position, string_to_put):
        return string[:position] + string_to_put + string[position:]

    def print_stages(self):
        self.stage_tracker.print_stages()


#  p = JenkinsFileParser()
#  h = JenkinsFileHelper(p)
#  s = h.stage_tracker.get_stage('Deploy to dev-apps')
#  print(s)
#  ss = s.children[0]
#  print(ss)
#  h.process_stage(ss)
