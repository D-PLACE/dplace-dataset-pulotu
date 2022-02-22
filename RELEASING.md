# Releasing dplace-dataset-pulotu

1. Update the data in `raw/` running
   ```shell
   cldfbench download cldfbench_pulotu.py
   ```
2. Re-create the CLDF data running
   ```shell
   cldfbench makecldf --with-cldfreadme cldfbench_pulotu.py --glottolog-version v4.5
   ```
3. Make sure the CLDF is valid:
   ```shell
   pytest
   ```
4. Create metadata for Zenodo:
   ```shell
   cldfbench zenodo cldfbench_pulotu.py --communities dplace
   ```
5. Create flat CSV:
   ```shell
   cldfbench pulotu.flatcsv
   ```
6. Create the release commit:
   ```shell
   git commit -a -m "release <VERSION>"
   ```
7. Create a release tag:
   ```
   git tag -a v<VERSION> -m"<VERSION> release"
   ```
8. Create a release from this tag on https://github.com/D-PLACE/dplace-dataset-pulotu/releases
9. Verify that data and metadata has been picked up by Zenodo correctly,
   and copy the citation information into the GitHub release description.

