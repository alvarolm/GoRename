GoRename [![documentation](https://img.shields.io/badge/info-documentation-blue.svg)](http://alvarolm.github.io/GoRename/)
=========

GoRename is a Golang plugin for [SublimeText](http://www.sublimetext.com/) 3 that integrates the Go [gorename](https://godoc.org/golang.org/x/tools/cmd/gorename) tool.

```
The gorename command performs precise type-safe renaming of identifiers in Go source code.
```
useful for refactoring.

(based on previus work from [waigani](http://github.com/waigani/GoOracle))

Usage
-----

1) Place the cursor over the identifier you want to rename (could be a variable, method, etc.).

2) press CTRL+ALT+R, then using the up and down keys select the optional flags to be used with ENTER, once you're done press ESC or click away.

3) type the new name and press ENTER.

4) review the parameters and press ENTER again to confirm and execute the gorename tool.

(If by any chance the results panel disappears just press CTRL+SHIFT+ALT+R)

configurable flags:
```
-force     causes the renaming to proceed even if conflicts were reported.
           The resulting program may be ill-formed, or experience a change
           in behaviour.

           WARNING: this flag may even cause the renaming tool to crash.
           (In due course this bug will be fixed by moving certain
           analyses into the type-checker.)

-d         display diffs instead of rewriting files

-v         enables verbose logging.
```

Install
-------

Install Sublime Package Control (if you haven't done so already) from http://wbond.net/sublime_packages/package_control. Be sure to restart ST to complete the installation.

Bring up the command palette (default ctrl+shift+p or cmd+shift+p) and start typing Package Control: 'Install Package' then press return or click on that option to activate it. You will be presented with a new Quick Panel with the list of available packages. Type 'GoRename' and press return or click on its entry to install GoRename. If there is no entry for 'GoRename', you most likely already have it installed.

GoOracle has several variables to be set in order to work. These are explained in the comments of the default settings `Preferences > Package Settings > GoOracle > Settings-Default`:

```javascript
{
	// rename files that had been modified after the 'go_rename' command has been executed.
	// (DO NOT set to true unless you want a renaming nightmare)
	"rename_modified_files": false,

	// use golangconfig, if false then shellenv will be used to get golang environment variables
	"use_golangconfig": false,

	// env overwrites the default shell environment vars
	// e.g "env": { "GOPATH": "$HOME/go/bin:$PATH" }
	"env": {},

	// The output can either be one of: 'buffer', 'output_panel'
	// Buffers can hold results from more than one invocation
	// Output panels sit underneath the editor area and are easily dismissed
	"output": "output_panel",

	// print debug info to the terminal
	"debug": false,

	// guru_scope is an array of scopes of analysis for guru.
	// e.g (for github.com/juju/juju) "guru_scope": ["github.com/juju/juju/cmd/juju", "github.com/juju/juju/cmd/jujud"]
	"gorename_scope": [],
}
```
You set your own variables in `Preferences > Package Settings > GoRename > Settings-User`.

You can also make project specific settings. First save your current workspace as a project `Project > Save as project ...`, then edit your project `Project > Edit Project`. Below is an example which sets up GoOracle to be used on the [github.com/juju/juju](https://github.com/juju/juju) codebase:

```javascript
{
    "folders":
    [
        {
            "follow_symlinks": true,
            "path": "/home/user/go/src/github.com/juju/juju"
        }
    ],
    "settings":
    {
        "GoRename": {
            "gorename_scope": ["github.com/juju/juju/cmd/juju", "github.com/juju/juju/cmd/jujud"],
            "output": "output_panel"
        }
    },
}
```

Default key binding:

```javascript
[
    { "keys": ["ctrl+alt+r"], "command": "go_rename"},
    { "keys": ["ctrl+alt+shift+r"], "command": "go_rename_show_results"},

	{ "keys": ["enter"], "command": "go_rename_confirm", "context": 
	[{ "key": "selector", "operator": "equal", "operand": "text.gorename-results" }]
	}
]
```

You can set your own key binding by copying the above into `Preferences > Keybindings - User` and replacing ctrl+shift+g with your preferred key(s).


Dependencies
------------
GoRename relies on the gorename tool. You must install it in order for Gorename to work. Run the following on your command line:

`go get -u golang.org/x/tools/cmd/gorename`



Copyright, License & Contributors
=================================

GoRename is released under the MIT license. See [LICENSE.md](LICENSE.md)

GoRename is the copyrighted work of *The GoRename Authors* i.e me ([alvarolm](https://github.com/alvarolm/GoRename)) and *all* contributors. If you submit a change, be it documentation or code, so long as it's committed to GoRename's history I consider you a contributor. See [AUTHORS.md](AUTHORS.md) for a list of all the GoRename authors/contributors.
