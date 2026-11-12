import time
import requests
import re
import json

class YouTubeLiveChatReader:
    def __init__(self, video_id: str):
        self.video_id = video_id
        self.api_key = None
        self.client_version = None
        self.continuation = None
        self.seen_ids = set()
        self.session = requests.Session()
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36',
            'Accept-Language': 'en-US,en;q=0.9',
            'Origin': 'https://www.youtube.com',
            'Referer': 'https://www.youtube.com/'
        }

    def initialize(self) -> bool:
        url = f'https://www.youtube.com/live_chat?v={self.video_id}'
        try:
            resp = self.session.get(url, headers=self.headers, timeout=10)
            if resp.status_code != 200:
                print(f"[YT-READER] Gagal membuka live chat page (Status: {resp.status_code})")
                return False

            text = resp.text
            m_key = re.search(r'\"INNERTUBE_API_KEY\":\"([^\"]+)\"', text)
            m_ver = re.search(r'\"INNERTUBE_CLIENT_VERSION\":\"([^\"]+)\"', text)

            if not m_key or not m_ver:
                print("[YT-READER] Tidak menemukan API Key atau Client Version di halaman YouTube.")
                return False

            self.api_key = m_key.group(1)
            self.client_version = m_ver.group(1)

            # Extract initial data
            prefix = 'ytInitialData\"] = '
            idx = text.find(prefix)
            if idx != -1:
                start = idx + len(prefix)
                data, _ = json.JSONDecoder().raw_decode(text[start:])
                lcr = data.get('contents', {}).get('liveChatRenderer', {})
                if 'messageRenderer' in data.get('contents', {}):
                    reason = data['contents']['messageRenderer'].get('text', {}).get('runs', [{}])[0].get('text', '')
                    print(f"[YT-READER] Pesan dari YouTube: {reason}")
                    return False

                # Extract initial continuations
                continuations = lcr.get('continuations', [])
                if continuations:
                    c_data = list(continuations[0].values())[0]
                    self.continuation = c_data.get('continuation')

                # Pre-populate seen_ids from initial actions
                for a in lcr.get('actions', []):
                    item = a.get('addChatItemAction', {}).get('item', {})
                    r = item.get('liveChatTextMessageRenderer') or item.get('liveChatPaidMessageRenderer')
                    if r and 'id' in r:
                        self.seen_ids.add(r['id'])

            if not self.continuation:
                # Fallback to regex
                conts = re.findall(r'\"continuation\":\"([^\"]+)\"', text)
                if conts:
                    self.continuation = conts[0]

            print(f"[YT-READER] Berhasil terhubung ke live chat stream {self.video_id}!")
            return bool(self.continuation)
        except Exception as e:
            print(f"[YT-READER] Error saat inisialisasi: {e}")
            return False

    def fetch_new_messages(self):
        """Mengambil pesan chat baru. Mengembalikan list of (author, message)"""
        if not self.continuation or not self.api_key:
            if not self.initialize():
                return []

        url = f'https://www.youtube.com/youtubei/v1/live_chat/get_live_chat?key={self.api_key}'
        payload = {
            'context': {
                'client': {
                    'clientName': 'WEB',
                    'clientVersion': self.client_version
                }
            },
            'continuation': self.continuation
        }

        try:
            resp = self.session.post(url, json=payload, headers=self.headers, timeout=10)
            if resp.status_code != 200:
                print(f"[YT-READER] API get_live_chat mengembalikan status {resp.status_code}")
                # Reset continuation to force re-init next time
                self.continuation = None
                return []

            data = resp.json()
            cont_contents = data.get('continuationContents', {}).get('liveChatContinuation', {})
            actions = cont_contents.get('actions', [])
            
            new_messages = []
            for a in actions:
                item = a.get('addChatItemAction', {}).get('item', {})
                r = item.get('liveChatTextMessageRenderer') or item.get('liveChatPaidMessageRenderer')
                if r:
                    msg_id = r.get('id', '')
                    if msg_id and msg_id in self.seen_ids:
                        continue
                    if msg_id:
                        self.seen_ids.add(msg_id)

                    author = r.get('authorName', {}).get('simpleText', 'Penonton')
                    if author.startswith('@'):
                        author = author[1:]
                    runs = r.get('message', {}).get('runs', [])
                    msg_text = ''.join(run.get('text', '') for run in runs)
                    if msg_text.strip():
                        new_messages.append((author, msg_text.strip()))

            # Update continuation
            continuations = cont_contents.get('continuations', [])
            if continuations:
                c_data = list(continuations[0].values())[0]
                self.continuation = c_data.get('continuation')
            else:
                self.continuation = None

            return new_messages
        except Exception as e:
            print(f"[YT-READER] Error fetching messages: {e}")
            self.continuation = None
            return []

if __name__ == "__main__":
    reader = YouTubeLiveChatReader("xMU5DlRosEQ")
    if reader.initialize():
        print("Initialized OK, waiting 2s then fetching...")
        time.sleep(2)
        msgs = reader.fetch_new_messages()
        print(f"Fetched {len(msgs)} new messages: {msgs}")
