import pyautogui
import pyperclip
import time
import subprocess
import os

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
    if not os.path.isfile(file_path):
        raise FileNotFoundError(f"File not found: {file_path}")
    with open(file_path, 'r', encoding='utf-8') as file:
        return file.read()
# Mengirim pesan ke chat room
def send_messages():
    # Tunggu beberapa detik untuk memastikan jendela chat aktif
    time.sleep(3)
    
    # Path ke file textpromo.txt
    base_path = os.path.expanduser('~/Documents/Python/telegrambot/')
    file_path = os.path.join(base_path, 'textpromo.txt')
    file_path2 = os.path.join(base_path, 'textpromo2.txt')
    try:
        # Baca teks dari file
        promo_text = read_text_from_file(file_path)
        promo_text2 = read_text_from_file(file_path2)
    except FileNotFoundError as e:
        print(e)
        return
    
    for i in range(1, 101):
        # Kirim pesan "/next"
        pyautogui.typewrite("/next")
        pyautogui.press('enter')
        time.sleep(6)  # Jeda 3 detik

        message_lines = [""] 
        # Kirim setiap baris pesan
        for line in message_lines:
            pyautogui.typewrite(line)
            pyperclip.copy(promo_text)
            pyautogui.hotkey('ctrl', 'v')  
            pyautogui.press('enter')
            pyperclip.copy(promo_text2)
            pyautogui.hotkey('ctrl', 'v')  
            pyautogui.hotkey('shift', 'enter')  
            pyautogui.typewrite(format(i))
            time.sleep(0.5)  # Jeda kecil antara ketikan karakter

        # Kirim pesan
        pyautogui.press('enter')
        time.sleep(1)  # Jeda 1 detik

# Main execution
if __name__ == "__main__":
    open_telegram()  # Buka aplikasi Telegram
    send_messages()  # Kirim pesan
