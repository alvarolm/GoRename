# Copyright (c) 2014 Jesse Meek <https://github.com/waigani>
# Copyright (c) 2016 Alvaro Leiva <https://github.com/alvarolm>
# This program is Free Software see LICENSE file for details.

"""
GoRename is a Go gorename plugin for Sublime Text 3.
It depends on the gorename tool being installed:
go get -u golang.org/x/tools/cmd/gorename
"""

# TODO: review & clean

import sublime, sublime_plugin, subprocess, time, re, os, subprocess, sys, time, hashlib

DEBUG = False
VERSION = ''
use_golangconfig = False
# holds renaming parameters
renameMe = {}
runningTool = False

def log(*msg):
    print("GoRename:", msg[0:])

def debug(*msg):
    if DEBUG:
        print("GoRename [DEBUG]:", msg[0:])

def error(*msg):
        print("GoRename [ERROR]:", msg[0:])

def plugin_loaded():
    global DEBUG
    global VERSION
    global use_golangconfig

    DEBUG = get_setting("gorename_debug", False)
    use_golangconfig = get_setting("gorename_use_golangconfig", False)

    # load shellenv
    def load_shellenv():
        global shellenv
        from .dep import shellenv

    # try golangconfig
    if use_golangconfig:
        try:
            global golangconfig
            import golangconfig    
        except:
            error("couldn't import golangconfig:", sys.exc_info()[0])
            log("using shellenv instead of golangconfig")
            use_golangconfig = False
            load_shellenv()
        
    else:
        load_shellenv()

    log("debug:", DEBUG)
    log("use_golangconfig", use_golangconfig)

    # keep track of the version if possible (pretty nasty workaround, any other ideas ?)
    try:
        PluginPath = os.path.dirname(os.path.realpath(__file__))
        p = subprocess.Popen(["git", "describe", "master", "--tags"], stdout=subprocess.PIPE, cwd=PluginPath)
        GITVERSION = p.communicate()[0].decode("utf-8").rstrip()
        if p.returncode != 0:
             debug("git return code", p.returncode)
             raise Exception("git return code", p.returncode) 


        defsettings = os.path.join(PluginPath, 'Default.sublime-settings')
        f = open(defsettings,'r')
        filedata = f.read()
        f.close()
        newdata = filedata.replace(get_setting('gorename_version'), GITVERSION+'_')
        f = open(defsettings,'w')
        f.write(newdata)
        f.close()
    except:
        debug("couldn't get git tag:", sys.exc_info()[0])

    # read version
    VERSION = sublime.load_settings('Default.sublime-settings').get('gorename_version')
    log("version:", VERSION)

    # check if user setting exists and creates it
    us = sublime.load_settings("GoRename.sublime-settings")
    if (not us.has('gorename_debug')):
        us.set('gorename_debug', DEBUG)
        sublime.save_settings("GoRename.sublime-settings")

class GoRenameCommand(sublime_plugin.TextCommand):
    def __init__(self, view):
        self.view = view 
        # ...
    def run(self, edit, simulate=False, force=False, verbose=False):

        try:
            current_selection = self.view.sel()
            region = current_selection[0]
            text = self.view.substr(sublime.Region(0, region.end()))
            cb_map = self.get_map(text)
            byte_end = cb_map[sorted(cb_map.keys())[-1]]
            byte_begin = None

            if not region.empty(): 
                byte_begin = cb_map[region.begin()-1]
            else:
                byte_begin = byte_end
        except:
            sublime.error_message('GoRename:\nCouldn\'t get cursor positon, make sure that the Go source file is saved and the cursor is over the identifier (variable, function ...) you want to query.')
            error("couldn't cursor position: ", sys.exc_info()[0])
        
        word = self.view.substr(self.view.word(region.begin())).rstrip()
        position = self.view.rowcol(region.begin())
        line_number = position[0]+1
        del position
        line_string = self.view.substr(self.view.line(region))



        # TODO: improve preliminary identifier validation
        if len(word) == 0:
            self.view.show_popup('<b>Gorename</b>:<br/> Invalid identifier:\nno identifier here.')
            return

        message = 'Running GoRename %s:\nFrom %s to %s\n[Line Number: %s][Byte Offset: %s]\nFlags: %s\nReference:\n%s'

        global s, f, v, flags
        s = simulate
        f = force
        v = verbose
        flags = ''

        def compile_flags(only_enabled=False): # and construct flags argument
            compiled_flags_array = []
            enabledTitle = 'ENABLED: '
            if only_enabled:
                enabledTitle = ''
            global flags

            # reset 
            flags = ''

            if s:
                compiled_flags_array.append(enabledTitle+'Simulate (-d)')
                flags = '-d '
            elif not only_enabled:
                compiled_flags_array.append('DISABLED: Simulate (-d)')

            if f:
                compiled_flags_array.append(enabledTitle+'force (-force)')
                flags = flags + '-force '
            elif not only_enabled:
                compiled_flags_array.append('DISABLED: force (-force)')

            if v:
                compiled_flags_array.append(enabledTitle+'verbose (-v)')
                flags = flags + '-v'
            elif not only_enabled:
                compiled_flags_array.append('DISABLED: verbose (-v)')
            return compiled_flags_array
            
        def rename_name_input(name):
            debug('flags:', flags)

            global renameMe
            renameMe['compiled_message'] = message % ('%s',word, name, line_number, byte_begin, compile_flags(True), line_string)
            self.write_running(renameMe['compiled_message'] % ('[press ENTER to continue]'), True, True) 
            renameMe['offset'] = byte_begin
            renameMe['name'] = name
            renameMe['flags'] = flags
            renameMe['file_path'] = self.view.file_name()
            renameMe['checksum'] = hashlib.sha256(open(renameMe['file_path'],'rb').read()).hexdigest() 

        def popup_menu_callback(flag_opt):
            global s,f,v
            if flag_opt == 0:
                s = not s 
            elif flag_opt == 1:
                f = not f
            elif flag_opt == 2:
                v = not v
            if flag_opt != -1:
                pop_menu()
            else: 
                self.view.window().show_input_panel('GoRename: rename "%s" (from line %s) to' % (word, line_number), word, rename_name_input, on_change=None, on_cancel=None)

        def pop_menu():
            self.view.show_popup_menu(compile_flags(), popup_menu_callback)

        pop_menu()

        

    def gorename_complete(self, out, err, focus=False):
        self.write_out(out, err)

    def write_running(self, content, readonly=False, focus=False):
        """ Write the "Running..." header to a new file and focus it to get results
        """

        #window = self.view.window()
        window = sublime.active_window()
        view = get_output_view(window)
        view.set_read_only(False)

        # Run a new command to use the edit object for this view.
        view.run_command('go_rename_write_running', {'content': content})

        if get_setting("gorename_output", "buffer") == "output_panel":
            window.run_command('show_panel', {'panel': "output." + view.name() })
        else:
            window.focus_view(view)

        view.set_read_only(readonly)

        # focus no matter what
        if focus:
            window.focus_view(view)

    def write_out(self, result, err):

        """ Write the gorename output to a new file.
        """

        #window = self.view.window()
        window = sublime.active_window()
        view = get_output_view(window)
        
        # Run a new command to use the edit object for this view.
        view.run_command('go_rename_write_results', {
            'result': result,
            'err': err})

        if get_setting("gorename_output", "buffer") == "output_panel":
            window.run_command('show_panel', {'panel': "output." + view.name() })
        else:
            window.focus_view(view)

    def get_map(self, chars):
        """ Generate a map of character offset to byte offset for the given string 'chars'.
        """

        byte_offset = 0
        cb_map = {}

        for char_offset, char in enumerate(chars):
            cb_map[char_offset] = byte_offset
            byte_offset += len(char.encode('utf-8'))
            if char == '\n' and self.view.line_endings() == "Windows":
                byte_offset += 1
        return cb_map

    def gorename(self, file_path, begin_offset=None, flags=None, name=None, callback=None):
        """ Builds the gorename shell command and calls it, returning it's output as a string.
        """

        global runningTool
        runningTool = True

        pos = "#" + str(begin_offset)

        # golangconfig or shellenv ?
        cmd_env = ''
        if use_golangconfig:
            try:
                toolpath, cmd_env = golangconfig.subprocess_info('gorename', ['GOPATH', 'PATH'], view=self.view)
                toolpath = os.path.realpath(toolpath)
            except:
                error("golangconfig:", sys.exc_info())
                return
        else:
            toolpath = 'gorename'
            cmd_env = shellenv.get_env(for_subprocess=True)[1]
            cmd_env.update(get_setting("gorename_env", {}))

        debug("env", cmd_env)

        gorename_json = ""
        if get_setting("gorename_json", False):
            gorename_json = "-json"

        # Build gorename cmd.
        cmd = "%(toolpath)s -offset %(file_path)s:%(pos)s -to %(name)s %(flags)s" % {
        "toolpath": toolpath,
        "file_path": file_path,
        "pos": pos,
        "name": name,
        "flags": flags} 

        debug("cmd", cmd)

        sublime.set_timeout_async(lambda: self.runInThread(cmd, callback, cmd_env), 0)

    def runInThread(self, cmd, callback, env):
        proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, stdin=subprocess.PIPE, shell=True, env=env)
        out, err = proc.communicate()
        callback(out.decode('utf-8'), err.decode('utf-8'))
        global runningTool
        runningTool = False

class GoRenameConfirmCommand(sublime_plugin.TextCommand):
    """ Writes the gorename output to the current view.
    """

    def run(self, edit):
        global renameMe
        #view = self.view
        debug('Stored rename parameters:', renameMe)
        # check that the referenced file hasn't changed

        if (len(renameMe)==0):
            sublime.error_message("Invalid GoRename parameters")
        if (runningTool == False):
            if ((hashlib.sha256(open(renameMe['file_path'],'rb').read()).hexdigest() != renameMe['checksum']) and (get_setting('gorename_rename_modified_files', False) == False)):
                sublime.error_message("Couldn't execute gorename, the referenced file has changed, please start over.")
                # reset renameMe
                renameMe = {}
            else:
                GR = GoRenameCommand(self)
                GR.write_running(renameMe['compiled_message'] % ('[Running...]'), True, True)
                GR.gorename(file_path=renameMe['file_path'] ,begin_offset=renameMe['offset'], name=renameMe['name'], flags=renameMe['flags'], callback=GR.gorename_complete)
                # reset renameMe
                renameMe = {}
        else:
            sublime.message_dialog("GoRename tool already executing")
        


class GoRenameWriteResultsCommand(sublime_plugin.TextCommand):
    """ Writes the gorename output to the current view.
    """

    def run(self, edit, result, err):
        view = self.view

        view.set_read_only(False)

        if result:
            view.insert(edit, view.size(), result)
        if err:
            errLen = view.insert(edit, view.size(), err)
        
        view.set_read_only(True)

        # reset
        global renameMe
        renameMe = {}
        

class GoRenameWriteRunningCommand(sublime_plugin.TextCommand):
    """ Writes the gorename output to the current view.
    """

    def run(self, edit, content):
        view = self.view

        view.set_viewport_position(view.text_to_layout(view.size() - 1))
        view.insert(edit, view.size(), content)


class GoRenameShowResultsCommand(sublime_plugin.TextCommand):
    def run(self, edit):
        if get_setting("gorename_output", "buffer") == "output_panel":
            self.view.window().run_command('show_panel', {'panel': "output.GoRename Output" })
        else:
            output_view = get_output_view(self.view.window())
            self.view.window().focus_view(output_view)


class GoRenameOpenResultCommand(sublime_plugin.EventListener):

    '''
    def on_modification(self, view):
        if view.name() == "GoRename Output":
            log("on modif")
    '''

    def on_selection_modified(self, view):
        if view.name() == "GoRename Output":
            if len(view.sel()) != 1:
                return
            if view.sel()[0].size() == 0:
                return

            lines = view.lines(view.sel()[0])
            if len(lines) != 1:
                return

            line = view.full_line(lines[0])
            text = view.substr(line)

            format = get_setting("gorename_format")

            # "filename:line:col" pattern for json
            m = re.search("\"([^\"]+):([0-9]+):([0-9]+)\"", text)

            # >filename:line:col< pattern for xml
            if m == None:
                m = re.search(">([^<]+):([0-9]+):([0-9]+)<", text)

            # filename:line.col-line.col: pattern for plain
            if m == None:
                m = re.search("^([^:]+):([0-9]+).([0-9]+)[-: ]", text)
            
            if m:
                w = view.window()
                new_view = w.open_file(m.group(1) + ':' + m.group(2) + ':' + m.group(3), sublime.ENCODED_POSITION)
                group, index = w.get_view_index(new_view)
                if group != -1:
                    w.focus_group(group)


def get_output_view(window):
    view = None
    buff_name = 'GoRename Output'

    if get_setting("gorename_output", "buffer") == "output_panel":
        view = window.create_output_panel(buff_name)
    else:
        # If the output file is already open, use that.
        for v in window.views():
            if v.name() == buff_name:
                view = v
                break
        # Otherwise, create a new one.
        if view is None:
            view = window.new_file()

    view.set_name(buff_name)
    view.set_scratch(True)
    view_settings = view.settings()
    view_settings.set('line_numbers', False)
    view.set_syntax_file('Packages/GoRename/GoRenameResults.tmLanguage')

    return view

def get_setting(key, default=None):
    """ Returns the setting in the following hierarchy: project setting, user setting, 
    default setting.  If none are set the 'default' value passed in is returned.
    """

    val = None
    try:
       val = sublime.active_window().active_view().settings().get('GoRename', {}).get(key)
    except AttributeError:
        pass

    if not val:
        val = sublime.load_settings("GoRename.sublime-settings").get(key)
    if not val:
        val = sublime.load_settings("Default.sublime-settings").get(key)
    if not val:
        val = default
    return val