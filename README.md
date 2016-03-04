# SimServer #

SimServer hosts MATLAB simulations on a server, and exposes an HTTP API and Web Dashboard for you to control the simulations with.
Ideally suited for scientific app development with an existing MATLAB codebase.
It more generally allows you to RPC to any running MATLAB script, and even remotely eval MATLAB code.

## Status ##

This was developed for a clinical trial in Diabetes R&D at Roche.
Since the trial was completed, I stripped the sensitive info and
reorganized the code. It hasn't been thoroughly tested since, but worked well at one point,
and it wouldn't be much more effort on my end to test, remove hardcoded paths, and write up an install guide.

If this is a project you're interested in using - send me an email, and we can probably make it work.

Email: karanssikka@gmail.com

## How to use ##

- Install the MATLAB runner (simserver.py) on a machine with MATLAB installed.
- Install the SimServer web app on a machine exposed to the internet (works in the cloud).
- Set up an SSH tunnel so that the web app can bind to the MATLAB runner.
- Navigate to the SimServer web app in your browser to upload and run a simulation!

## Simulation File Format ##

See `SimWrapper.m` for an example.
