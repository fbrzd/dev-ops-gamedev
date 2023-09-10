# Dev Ops
Copy "Builder.cs" at "Asset/Editor"

## Run
python autobuild.py [flags] <platform> <version>

## Examples
Itchio Windows: python autobuild.py -build -compress -deploy-prod windows <version>
Itchio Linux: python autobuild.py -build -compress -deploy-prod linux <version>
Itchio Android: python autobuild.py -build -deploy-prod android <version>
Google: python autobuild.py -build -deploy-prod google <version>
