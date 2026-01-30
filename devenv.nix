{ pkgs, lib, config, devenv-zsh, inputs, ... }:

{
  cachix.pull = [ "devenv" ];
  # https://devenv.sh/languages/
  imports = [ devenv-zsh.plugin ];
  zsh.enable = true;

  # 1. Enable Python
  languages.python = {
    enable = true;
    version = "3.13";
  };

  # Add the Google GenAI SDK
  packages = [ pkgs.python313Packages.google-genai ];

  # 2. Define the script wrapper
  scripts.extract-recipes.exec = "python main.py $@";

  # Optional: specific pre-commit hooks for both languages
  git-hooks.hooks = {
    black.enable = true; # Python formatter
    trim-trailing-whitespace.enable = true;
  };

  # 4. Shell welcome message
  enterShell = ''
    echo "🍳 Paprika to Cooklang Converter Environment"
    echo "Run 'extract-recipes <file.paprikarecipes>' to start."
  '';
}

