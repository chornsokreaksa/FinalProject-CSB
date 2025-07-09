# FinalProject-CSB
SSTI detection and exploitation tool.

## Installation
- Clone: git clone https://github.com/chornsokreaksa/FinalProject-CSB.git
- Install: pip install requests
- Run Flask: python app.py

## Usage
- Detect: python ssti.py -u http://localhost:80/page
- Exploit: python ssti.py -u http://localhost:80/page -i --os-cmd whoami
