import pyautogui
import time
import platform

# Fungsi untuk mencari dan membuka aplikasi Telegram melalui tombol pencarian Windows
def open_telegram():
    if platform.system() != "Windows":
        raise Exception("Skrip ini hanya mendukung Windows")
    # Tekan tombol Windows untuk membuka menu Start
    pyautogui.press('win')
    time.sleep(1)  # Jeda 1 detik untuk memastikan menu Start terbuka

    # Ketik "Telegram" untuk mencari aplikasi
    pyautogui.typewrite("Telegram")
    time.sleep(1)  # Jeda 1 detik untuk hasil pencarian muncul

    # Tekan Enter untuk membuka aplikasi Telegram
    pyautogui.press('enter')
    time.sleep(1)  # Tunggu beberapa detik agar aplikasi Telegram terbuka sepenuhnya

# Mengirim pesan ke chat room
def send_messages():
    # Tunggu beberapa detik untuk memastikan jendela chat aktif
    time.sleep(1)

    for i in range(1, 151):
        # Kirim pesan "/next"
        pyautogui.typewrite("/next")
        pyautogui.press('enter')
        time.sleep(3)  # Jeda 3 detik

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
        time.sleep(1)  # Jeda 3 detik

# Main execution
if __name__ == "__main__":
    open_telegram()  # Buka aplikasi Telegram
    send_messages()  # Kirim pesan
