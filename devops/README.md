# Dev Ops
Copy "Build.cs" at "Asset/Editor"

## Run
python autobuild.py [flags] <platform> <version>

## Examples
Itchio Windows: python autobuild.py -build -compress -deploy-prod windows v0.0.1
Itchio Linux: python autobuild.py -build -compress -deploy-prod linux v0.0.1
Itchio Android: python autobuild.py -build -deploy-prod android v0.0.1
Google: python autobuild.py -build -deploy-prod google v0.0.1
