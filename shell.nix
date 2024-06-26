with (import <nixpkgs> {});
let
  mach-nix = import (builtins.fetchGit {
    url = "https://github.com/DavHau/mach-nix";
    ref = "refs/tags/3.5.0";
  }) {};
  pyEnv = mach-nix.mkPython rec {
    providers._default = "wheel,conda,nixpkgs,sdist";
    requirements = builtins.readFile ./requirements.txt;
  };
in

mach-nix.nixpkgs.mkShell {
  buildInputs = [
    # nanoBench build deps
    gnumake
    gcc
    
    # python deps
    virtualenv
    pyEnv
  ];
  venvDir = "venv3";
  shellHook = ''
    virtualenv --no-setuptools venv
    export PIP_PREFIX=$(pwd)/_build/pip_packages
    export PATH=$PWD/venv/bin:$PATH
    export PYTHONPATH=venv/lib/python3/site-packages/:$PYTHONPATH
    export PYTHONPATH="$PIP_PREFIX/${pkgs.python3.sitePackages}:$PYTHONPATH"
    export PATH="$PIP_PREFIX/bin:$PATH"
    unset SOURCE_DATE_EPOCH
    sh build.sh
  '';

   postShellHook = ''
     ln -sf ${pyEnv}/lib/python3/site-packages/* ./venv/lib/python3/site-packages
  '';
}
