with import <nixpkgs> { };
{ pkgs ? import <nixpkgs> { } }:
let 
  myPython = pkgs.python3;
  pythonPackages = pkgs.python3Packages;
  pythonWithPkgs = myPython.withPackages (pythonPkgs: with pythonPkgs; [
    ipython
    pip
    setuptools
    virtualenvwrapper
    wheel
  ]);

  # add the needed packages here
  extraBuildInputs = with pkgs; [
    myPython
    pythonPackages.numpy
    pythonPackages.pytest
    pythonPackages.pylint
    pythonPackages.pycparser
    pythonPackages.sphinx

    # needed for running tests
    gcc
    clang 
    gnumake
    cmake

    # needed for AssemblyLine
    autoconf
    automake
    libtool
    pkg-config

    # dev
    jetbrains.pycharm-community
  ] ++ (lib.optionals pkgs.stdenv.isLinux ([
  ]));
in
import ./python-shell.nix { 
  extraBuildInputs=extraBuildInputs; 
  myPython=myPython;
  pythonWithPkgs=pythonWithPkgs;
}
