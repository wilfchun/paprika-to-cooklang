{ pkgs, lib, config, devenv-zsh, inputs, ... }:

{
  cachix.pull = [ "devenv" ];
  # https://devenv.sh/languages/
  imports = [ devenv-zsh.plugin ];
  zsh.enable = true;

  # 1. Enable Python
  languages.python = {
    enable = true;
    version = "3.13"; # Or "3.12"

    # If you ever decide to add external libraries (like Pillow for images),
    # you can add them here without messing with pip manually.
    # venv.enable = true;
    # venv.requirements = ''
    #   requests
    # '';
  };

  # 2. Define the script wrapper
  scripts.extract-recipes.exec = "python main.py $@";

  # 3. Code Quality (Optional but recommended)
  pre-commit.hooks = {
    black.enable = true; # Auto-format python code
    trim-trailing-whitespace.enable = true;
  };

  # 4. Shell welcome message
  enterShell = ''
    echo "🍳 Paprika to Cooklang Converter Environment"
    echo "Run 'extract-recipes <file.paprikarecipes>' to start."
  '';
}
