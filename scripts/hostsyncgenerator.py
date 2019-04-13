#!/usr/bin/python3 -i
#
# Copyright (c) 2013-2019 The Khronos Group Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import re
import sys

from generator import OutputGenerator, write

# HostSynchronizationOutputGenerator - subclass of OutputGenerator.
# Generates AsciiDoc includes of the externsync parameter table for the
# fundamentals chapter of the API specification. Similar to
# DocOutputGenerator.
#
# ---- methods ----
# HostSynchronizationOutputGenerator(errFile, warnFile, diagFile) - args as for
#   OutputGenerator. Defines additional internal state.
# ---- methods overriding base class ----
# genCmd(cmdinfo)
class HostSynchronizationOutputGenerator(OutputGenerator):
    # Generate Host Synchronized Parameters in a table at the top of the spec
    def __init__(self,
                 errFile = sys.stderr,
                 warnFile = sys.stderr,
                 diagFile = sys.stdout):
        OutputGenerator.__init__(self, errFile, warnFile, diagFile)

    threadsafety = {'parameters': '', 'parameterlists': '', 'implicit': ''}

    def makeParameterName(self, name):
        return 'pname:' + name

    def makeFLink(self, name):
        return 'flink:' + name

    # Generate an include file
    #
    # directory - subdirectory to put file in
    # basename - base name of the file
    # contents - contents of the file (Asciidoc boilerplate aside)
    def writeInclude(self):

        if self.threadsafety['parameters'] is not None:
            # Create file
            filename = self.genOpts.directory + '/' + 'parameters.txt'
            self.logMsg('diag', '# Generating include file:', filename)
            fp = open(filename, 'w', encoding='utf-8')

            # Host Synchronization
            write(self.genOpts.conventions.warning_comment, file=fp)
            write('.Externally Synchronized Parameters', file=fp)
            write('****', file=fp)
            write(self.threadsafety['parameters'], file=fp, end='')
            write('****', file=fp)
            write('', file=fp)

        if self.threadsafety['parameterlists'] is not None:
            # Create file
            filename = self.genOpts.directory + '/' + '/parameterlists.txt'
            self.logMsg('diag', '# Generating include file:', filename)
            fp = open(filename, 'w', encoding='utf-8')

            # Host Synchronization
            write(self.genOpts.conventions.warning_comment, file=fp)
            write('.Externally Synchronized Parameter Lists', file=fp)
            write('****', file=fp)
            write(self.threadsafety['parameterlists'], file=fp, end='')
            write('****', file=fp)
            write('', file=fp)

        if self.threadsafety['implicit'] is not None:
            # Create file
            filename = self.genOpts.directory + '/' + '/implicit.txt'
            self.logMsg('diag', '# Generating include file:', filename)
            fp = open(filename, 'w', encoding='utf-8')

            # Host Synchronization
            write(self.genOpts.conventions.warning_comment, file=fp)
            write('.Implicit Externally Synchronized Parameters', file=fp)
            write('****', file=fp)
            write(self.threadsafety['implicit'], file=fp, end='')
            write('****', file=fp)
            write('', file=fp)

        fp.close()

    # Check if the parameter passed in is a pointer to an array
    def paramIsArray(self, param):
        return param.get('len') is not None

    # Check if the parameter passed in is a pointer
    def paramIsPointer(self, param):
        ispointer = False
        paramtype = param.find('type')
        if paramtype.tail is not None and '*' in paramtype.tail:
            ispointer = True

        return ispointer

    # Turn the "name[].member[]" notation into plain English.
    def makeThreadDereferenceHumanReadable(self, dereference):
        matches = re.findall(r"[\w]+[^\w]*",dereference)
        stringval = ''
        for match in reversed(matches):
            if '->' in match or '.' in match:
                stringval += 'member of '
            if '[]' in match:
                stringval += 'each element of '

            stringval += 'the '
            stringval += self.makeParameterName(re.findall(r"[\w]+",match)[0])
            stringval += ' '

        stringval += 'parameter'

        return stringval[0].upper() + stringval[1:]

    def makeThreadSafetyBlocks(self, cmd, paramtext):
        protoname = cmd.find('proto/name').text

        # Find and add any parameters that are thread unsafe
        explicitexternsyncparams = cmd.findall(paramtext + "[@externsync]")
        if explicitexternsyncparams is not None:
            for param in explicitexternsyncparams:
                externsyncattribs = param.get('externsync')
                paramname = param.find('name')
                for externsyncattrib in externsyncattribs.split(','):

                    tempstring = '* '
                    if externsyncattrib == 'true':
                        if self.paramIsArray(param):
                            tempstring += 'Each element of the '
                        elif self.paramIsPointer(param):
                            tempstring += 'The object referenced by the '
                        else:
                            tempstring += 'The '

                        tempstring += self.makeParameterName(paramname.text)
                        tempstring += ' parameter'

                    else:
                        tempstring += self.makeThreadDereferenceHumanReadable(externsyncattrib)

                    tempstring += ' in '
                    tempstring += self.makeFLink(protoname)
                    tempstring += '\n'


                    if ' element of ' in tempstring:
                        self.threadsafety['parameterlists'] += tempstring
                    else:
                        self.threadsafety['parameters'] += tempstring

        # Find and add any "implicit" parameters that are thread unsafe
        implicitexternsyncparams = cmd.find('implicitexternsyncparams')
        if implicitexternsyncparams is not None:
            for elem in implicitexternsyncparams:
                self.threadsafety['implicit'] += '* '
                self.threadsafety['implicit'] += elem.text[0].upper()
                self.threadsafety['implicit'] += elem.text[1:]
                self.threadsafety['implicit'] += ' in '
                self.threadsafety['implicit'] += self.makeFLink(protoname)
                self.threadsafety['implicit'] += '\n'

        # Add a VU for any command requiring host synchronization.
        # This could be further parameterized, if a future non-Vulkan API
        # requires it.
        if self.genOpts.conventions.is_externsync_command(protoname):
            self.threadsafety['implicit'] += '* '
            self.threadsafety['implicit'] += 'The sname:VkCommandPool that pname:commandBuffer was allocated from, in '
            self.threadsafety['implicit'] += self.makeFLink(protoname)
            self.threadsafety['implicit'] += '\n'

    # Command generation
    def genCmd(self, cmdinfo, name, alias):
        OutputGenerator.genCmd(self, cmdinfo, name, alias)

        # @@@ (Jon) something needs to be done here to handle aliases, probably

        self.makeThreadSafetyBlocks(cmdinfo.elem, 'param')

        self.writeInclude()