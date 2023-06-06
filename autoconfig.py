#ext
import os
import win32api
import fileinput
from psutil import process_iter

#own
from settings import jsonSetter
from data import Data

DEFAULT_CAMERA_SNAP = '[Space],[v]'
DEFAULT_CHAMPION_ONLY = '[Button 3]'
DEFAULT_PLAYER_ATTACK = '[a]'
DEFAULT_WALK_CLICK = '[Button 2]'
DEFAULT_RANGE = '[o]'
DEFAULT_ORBWALK = '[space]'
DEFAULT_LANECLEAR = '[v]'
DEFAULT_LASTHIT = '[c]'

options = {
    'EnableTargetedAttackMove':'1',
    'TargetChampionsOnlyAsToggle':'0',
    'evtCameraSnap':DEFAULT_CAMERA_SNAP,
    'evtChampionOnly':DEFAULT_CHAMPION_ONLY,
    'evtPlayerAttackMoveClick':DEFAULT_PLAYER_ATTACK,
    'evtPlayerMoveClick':DEFAULT_WALK_CLICK,
    'evtShowCharacterMenu':DEFAULT_RANGE
}

class Autoconfig:
    
    def __init__(self, settings_to_persist, persisted_settings):
        self.settings_to_persist = settings_to_persist
        self.persisted_settings = persisted_settings

    @staticmethod
    def clear_name(string):
        return string.strip().removeprefix('"name": "').removesuffix('",')
    
    @staticmethod
    def clear_value(string):
        return string.strip(" \n").removeprefix('"value": "').removesuffix('"')
    
    def remove_duplications(self):
        #Prevent key bugs.
        current_values = self.get_persisted_settings()
        duplications = dict()
        with open(self.persisted_settings) as persisted_settings:
            for index, line in enumerate(persisted_settings, 1):
                line = Autoconfig.clear_value(line)
                if not line.isdecimal() and '.' not in line:
                    for k, v in current_values.items():
                            #remove normal keys
                            if line == v and index != k:
                                duplications[index] = line
                            
                            #remove double bound keys
                            if (line.startswith(v) or line.endswith(v)) and index != k:
                                if not line.startswith(('[Alt]', '[Ctrl]')):
                                    duplications[index] = line
                            
                            #remove C for lasthit
                            if line == DEFAULT_LASTHIT:
                                duplications[index] = line

                            #remove V for laneclear
                            if line == DEFAULT_LANECLEAR:
                                duplications[index] = line

                            #remove SPACE for orbwalk
                            if line == DEFAULT_ORBWALK:
                                duplications[index] = line

        for line in fileinput.input(self.persisted_settings, inplace=True):
            current_index = fileinput.lineno()
            for k, v in duplications.items():
                if current_index == k:
                    line = line.replace(v, '[<Unbound>],[<Unbound>]')
            print(line, end="")

    def get_persisted_settings(self):
        current_settings = dict()
        is_value = False
        value_pos = None
        with open(self.persisted_settings, "r+") as persisted_settings:
            for index, line in enumerate(persisted_settings, 1):
                line_name = Autoconfig.clear_name(line)
                if line_name in options.keys():
                    value_pos = index + 1
                    is_value = True
                    continue
                if is_value:
                    current_settings[value_pos] = Autoconfig.clear_value(line)
                    is_value = False
        return current_settings
        

    def set_persisted_settings(self):
        current_settings = self.get_persisted_settings()
        for line in fileinput.input(self.persisted_settings, inplace=True):
            current_index = fileinput.lineno()
            for (value_pos, current_value), new_value in zip(current_settings.items(), options.values()):
                if value_pos == current_index:
                    line = line.replace(current_value, new_value)
            print(line, end="")
        self.remove_duplications()

    def toggle_settings_to_persist(self, statment):
        for line in fileinput.input(self.settings_to_persist, inplace=True):
            if statment:
                line = line.replace("false", "true")
            else:
                line = line.replace("true", "false")

            print(line, end="")

    def set_json_settings(self):
        jsonSetter().setKey('orbwalk', DEFAULT_ORBWALK.removeprefix('[').removesuffix(']'))
        jsonSetter().setKey('laneclear', DEFAULT_LANECLEAR.removeprefix('[').removesuffix(']'))
        jsonSetter().setKey('lasthit', DEFAULT_LASTHIT.removeprefix('[').removesuffix(']'))
        jsonSetter().setMode('orbwalk', 'Less Basic Attacks')
        jsonSetter().setMode('lasthit', 'Auto')
        jsonSetter().setSetting('autoconfig', False)
        jsonSetter().setSetting('ppc', False)
        jsonSetter().setSetting('ext_drawings', True)
        jsonSetter().setSetting('ext_track', True)
        jsonSetter().setSetting('ext_focus', True)
        jsonSetter().setSetting('ext_limited', False)
        jsonSetter().setSetting('freeze', False)

    def set_config(self):
        self.toggle_settings_to_persist(False)
        self.set_persisted_settings()
        self.toggle_settings_to_persist(True)
        self.set_json_settings()
        
def start_autoconfig():
    league_path = None
    for process in process_iter(['name', 'cwd']):
        if process.info['name'] == Data.client_name_executable:
            os.system('taskkill -f -im "{}"'.format(Data.game_name_executable))
            league_path = process.info['cwd']

    if league_path is not None and os.path.isdir(league_path):
        settings_to_persist = os.path.join(league_path, '../', Data.settings_to_persist_path)
        persisted_settings = os.path.join(league_path, '../', Data.persisted_settings_path)
        files_list = [settings_to_persist, persisted_settings]

        for file in files_list:
            #prevent read-only files. (first attempt)
            try:
                win32api.SetFileAttributes(file, 128)    
            except:
                #second attempt.
                try:
                    os.chmod(file, 0o777)
                except:
                    pass

        Autoconfig(settings_to_persist, persisted_settings).set_config()
