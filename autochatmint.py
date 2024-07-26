import pyautogui
import pyperclip
import time
import subprocess

# Fungsi untuk mencari dan membuka aplikasi Telegram melalui tombol pencarian Linux
def open_telegram():
    # Tekan tombol Super (biasanya Windows) untuk membuka menu aplikasi
    subprocess.run(['xdotool', 'key', 'Super'])
    time.sleep(1)  # Jeda 1 detik untuk memastikan menu aplikasi terbuka

    # Ketik "Telegram" untuk mencari aplikasi
    pyautogui.typewrite("Telegram")
    time.sleep(1)  # Jeda 1 detik untuk hasil pencarian muncul

    # Tekan Enter untuk membuka aplikasi Telegram
    pyautogui.press('enter')
    time.sleep(3)  # Tunggu beberapa detik agar aplikasi Telegram terbuka sepenuhnya

# Fungsi untuk membaca teks dari file dan mengembalikannya sebagai string
def read_text_from_file(file_path):
    with open(file_path, 'r', encoding='utf-8') as file:
        return file.read()

# Mengirim pesan ke chat room
def send_messages():
    # Tunggu beberapa detik untuk memastikan jendela chat aktif
    time.sleep(3)

    promo_text = read_text_from_file('textpromo.txt')
    promo_text2 = read_text_from_file('textpromo2.txt')
    
    for i in range(1, 2):
        # Kirim pesan "/next"
        pyautogui.typewrite("/next")
        pyautogui.press('enter')
        time.sleep(6)  # Jeda 3 detik

        pyperclip.copy(promo_text)

        # Kirim pesan promosi
        pyautogui.hotkey('ctrl', 'v')  # Tempel teks dari clipboard
        pyperclip.copy(promo_text2)
        pyautogui.hotkey('ctrl', 'v')  # Tempel teks dari clipboard
        pyautogui.hotkey('shift', 'enter')  # Tempel teks dari clipboard
        pyautogui.typewrite(format(i))
        time.sleep(0.5)  # Jeda kecil antara ketikan karakter

        # Kirim pesan
        pyautogui.press('enter')
        time.sleep(1)  # Jeda 1 detik

# Main execution
if __name__ == "__main__":
    open_telegram()  # Buka aplikasi Telegram
    send_messages()  # Kirim pesan
