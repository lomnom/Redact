# How to build this into a standalone executable
## Mac
### Preresquisites
```bash
pip3 install pyinstaller
brew install create-dmg
```
### Build
1. Create .app
```bash
pyinstaller --name 'Redact' \
            --icon 'Icon.ico' \
            --windowed  \
            Censor.py
```
2. Create .dmg
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
3. Within dist there will be a `Redact.dmg`, which is the final product
Credit: based on https://medium.com/@jackhuang.wz/in-just-two-steps-you-can-turn-a-python-script-into-a-macos-application-installer-6e21bce2ee71

> Others pending