import pyautogui
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

# Mengirim pesan ke chat room
def send_messages():
    # Tunggu beberapa detik untuk memastikan jendela chat aktif
    time.sleep(3)

    for i in range(1, 101):
        # Kirim pesan "/next"
        pyautogui.typewrite("/next")
        pyautogui.press('enter')
        time.sleep(6)  # Jeda 3 detik

        # Kirim pesan promosi dengan newline menggunakan Shift+Enter
        message_lines = [""] # Digantikan dengan nomor
        
        # Kirim setiap baris pesan
        for line in message_lines:
            pyautogui.typewrite(line)
            pyautogui.hotkey('ctrl', 'v')  # Gunakan Shift+Enter untuk newline
            pyautogui.typewrite(format(i))
            time.sleep(0.5)  # Jeda kecil antara ketikan karakter

        # Kirim pesan
        pyautogui.press('enter')
        time.sleep(1)  # Jeda 1 detik

# Main execution
if __name__ == "__main__":
    open_telegram()  # Buka aplikasi Telegram
    send_messages()  # Kirim pesan
