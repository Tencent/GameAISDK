# -*- coding: utf-8 -*-
"""
This source code file is licensed under the GNU General Public License Version 3.
For full details, please refer to the file "LICENSE.txt" which is provided as part of this source code package.
Copyright (C) 2020 THL A29 Limited, a Tencent company.  All rights reserved.
"""

import os
import sys
import configparser

AI_SDK_PATH = '../../../../'
AGENT_AI_CFG_PATH = os.path.join(AI_SDK_PATH, 'cfg/task/agent/AgentAI.ini')
PLUGIN_CODE_PATH = os.path.join(AI_SDK_PATH, 'src/PlugIn/ai')

class TConfigParser(configparser.ConfigParser):
    """
    set ConfigParser options for case sensitive.
    """
    def __init__(self, defaults=None):
        configparser.ConfigParser.__init__(self, defaults=defaults)

    def optionxform(self, optionstr):
        return optionstr

class Generator(object):
    def __init__(self):
        pass

    def Generate(self, gameName, templateName):
        if not self._GeneratePluginCfg(gameName):
            return

        templateDir = os.path.join('.', templateName)
        codeDir = os.path.join(PLUGIN_CODE_PATH, gameName)
        if not self._GeneratePluginCode(gameName, templateDir, codeDir):
            return

    def _GeneratePluginCfg(self, gameName):
        try:
            config = TConfigParser()
            config.read(AGENT_AI_CFG_PATH)

            envSection = 'AGENT_ENV'
            aiSection = 'AI_MODEL'
            runSection = 'RUN_FUNCTION'

            config.set(envSection, 'UsePluginEnv', '1')
            config.set(envSection, 'EnvPackage', gameName)
            config.set(envSection, 'EnvModule', gameName + 'Env')
            config.set(envSection, 'EnvClass', gameName + 'Env')
            config.set(aiSection, 'UsePluginAIModel', '1')
            config.set(aiSection, 'AIModelPackage', gameName)
            config.set(aiSection, 'AIModelModule', gameName + 'AI')
            config.set(aiSection, 'AIModelClass', gameName + 'AI')
            config.set(runSection, 'UseDefaultRunFunc', '1')

            with open(AGENT_AI_CFG_PATH, 'w') as configfile:
                config.write(configfile)
        except Exception as e:
            print('_GeneratePluginCfg error: {}'.format(e))
            return False

        return True

    def _GeneratePluginCode(self, gameName, templateDir, codeDir):
        try:
            os.makedirs(codeDir, exist_ok=True)

            for filename in os.listdir(templateDir):
                if filename.startswith('.'):
                    continue

                fullPathName = os.path.join(templateDir, filename)
                if os.path.isdir(fullPathName):
                    subTemplateDir = fullPathName
                    subCodeDir = os.path.join(codeDir, filename)
                    self._GeneratePluginCode(gameName, subTemplateDir, subCodeDir)

                if os.path.isfile(fullPathName) and filename.endswith('.txt'):
                    codeFileName = filename.replace('XXX', gameName).replace('txt', 'py')
                    fullCodeFileName = os.path.join(codeDir, codeFileName)
                    if os.path.isfile(fullCodeFileName):
                        print('{} already exists!'.format(fullCodeFileName))
                        continue
                    self._DupCodeFromTemplate(gameName, fullPathName, fullCodeFileName)
        except Exception as e:
            print('_GeneratePluginCode {} --> {} error: {}'.format(templateDir, codeDir, e))
            return False

        return True

    def _DupCodeFromTemplate(self, gameName, srcFile, destFile):
        fileText = self._ReadFile(srcFile)
        fileText = fileText.replace('XXX', gameName)
        self._WriteFile(fileText, destFile)

    def _ReadFile(self, srcFile):
        fileText = None
        with open(srcFile, 'r', encoding='utf-8') as file:
            fileText = file.read()
        return fileText

    def _WriteFile(self, fileText, destFile):
        with open(destFile, 'w', encoding='utf-8') as file:
            file.write(fileText)

if __name__ == "__main__":
    g = Generator()
    g.Generate(sys.argv[1], sys.argv[2])