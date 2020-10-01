from cx_Freeze import setup, Executable

# Dependencies are automatically detected, but it might need
# fine tuning.
build_options = {'packages': [], 'excludes': []}

base = 'Console'

executables = [
    Executable('wingman-dl.py', base=base)
]

setup(name='wingman-dl',
      version = '1.0',
      description = 'Downloads CS:GO Wingman matches from your community profile',
      options = {'build_exe': build_options},
      executables = executables)
