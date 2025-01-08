# How to build this into a standalone executable
## Mac
### Preresquisites
```bash
pip3 install pyinstaller
brew install create-dmg
```
### Build
1. Make a virtualenv with only needed libraries 
```bash
python3 -m venv .
source ./bin/activate
pip3 install wxPython mss
```
2. Create .app
```bash
pyinstaller --name 'Redact' \
            --icon 'Icon.ico' \
            --windowed  \
            Censor.py
```
3. Create .dmg
```bash
cd dist
mkdir -p dmg
cp -r "Redact.app" dmg
create-dmg \
  --volname "Redact" \
  --volicon "../Icon.ico" \
  --window-pos 200 120 \
  --window-size 600 300 \
  --icon-size 100 \
  --icon "Redact.app" 175 120 \
  --hide-extension "Redact.app" \
  --app-drop-link 425 120 \
  "Redact.dmg" \
  "dmg/"
```
4. Cleanup (MAKE SURE YOU ARE WITHIN `dist` AND DOUBLE CHECK THE `rm` COMMAND TO NOT NUKE YOUR FILES!)
```bash
cd ..
deactivate
rm -rf bin build include lib
rm pyvenv.cfg Redact.spec
```
5. Within dist there will be a `Redact.dmg`, which is the final product. 

Credit: based on https://medium.com/@jackhuang.wz/in-just-two-steps-you-can-turn-a-python-script-into-a-macos-application-installer-6e21bce2ee71

> Others pending