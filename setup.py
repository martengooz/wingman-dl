from cx_Freeze import setup, Executable

# Dependencies are automatically detected, but it might need
# fine tuning.
build_options = {'packages': [], 'excludes': []}

base = 'Console'

executables = [
    Executable('download.py', base=base)
]

setup(name='wingman-dl',
      version = '1.0',
      description = 'Download CSGO Wingman demos from steam community',
      options = {'build_exe': build_options},
      executables = executables)
