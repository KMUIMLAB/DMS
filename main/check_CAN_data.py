import os
import time
import threading
import csv
import json

import can                           # python-can
import cantools                     # https://github.com/cantools/cantools
from config import config


def sniff_can_dbc(
    d_name: str,
    save_flag: bool,
    dataset_path: str,
    dbc_filename: str,
    can_bus,
    print_status: bool,
    stop_event: threading.Event
):
    """
    1) config['SAVE_PATH']/dbc 폴더에서 지정된 dbc_filename 로드
    2) can_bus.recv() 로부터 실제 프레임 수신
    3) 새로운 메시지 등장 시 메시지명+시그널명 콘솔 출력
    4) stop_event.set() 시 루프 종료 후 CSV/TXT 로 결과 저장
    """
    import os
    import csv
    import json

    print(f"[INFO] PID[{os.getpid()}] '{d_name}' listener started (DBC: {dbc_filename}).")

    # 1) DBC 로드
    CAN_basePath = os.path.join(config['SAVE_PATH'], 'dbc')
    dbc_path = os.path.join(CAN_basePath, dbc_filename)
    if not os.path.isfile(dbc_path):
        raise FileNotFoundError(f"DBC 파일이 없습니다: {dbc_path}")
    db = cantools.database.load_file(dbc_path)
    print(f"[INFO] Loaded {len(db.messages)} messages from '{dbc_filename}'")

    # 2) 저장 폴더 준비
    can_path = os.path.join(dataset_path, 'CAN')
    if save_flag and not os.path.isdir(can_path):
        os.makedirs(can_path)

    # 3) 모니터링 자료구조
    seen_msgs   = set()   # 이미 본 메시지 이름
    msg_signals = {}      # { msg_name: [sig1, sig2, ...] }

    print(f"[INFO] PID[{os.getpid()}] '{d_name}' start sniffing CAN bus...")
    # 4) CAN 수신 루프
    while not stop_event.is_set():
        try:
            frame = can_bus.recv()   # arbitration_id, data, timestamp…
        except Exception:
            break
        try:    
            msg = db.get_message_by_frame_id(frame.arbitration_id)
            if msg is None:
                continue

            # 새로운 메시지 탐지
            if msg.name not in seen_msgs:
                seen_msgs.add(msg.name)
                signals = [sig.name for sig in msg.signals]
                msg_signals[msg.name] = signals

                print("\n=== New CAN Message Detected ===")
                print(f"Message: {msg.name} (ID=0x{msg.frame_id:X}, DLC={msg.length})")
                # print("Signals:")
                # for s in signals:
                #    print(f"  - {s}")
                print("=" * 30)
        except:
            
            pass
    # 루프 종료
    print(f"\n[INFO] PID[{os.getpid()}] '{d_name}' sniffing stopped.")
    print(f"[INFO] Total unique messages: {len(seen_msgs)}")

    # 5) 결과 저장
    ts = time.strftime("%Y%m%d_%H%M%S")
    csv_path = os.path.join(can_path, f"{os.path.splitext(dbc_filename)[0]}_messages_{ts}.csv")
    with open(csv_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(["MessageName", "SignalNames"])
        for m, sig_list in msg_signals.items():
            writer.writerow([m, ";".join(sig_list)])
    print(f"[INFO] Saved CSV: {csv_path}")

    txt_path = os.path.join(can_path, f"{os.path.splitext(dbc_filename)[0]}_messages_{ts}.txt")
    with open(txt_path, 'w', encoding='utf-8') as f:
        json.dump(msg_signals, f, ensure_ascii=False, indent=2)
    print(f"[INFO] Saved TXT: {txt_path}")


if __name__ == "__main__":
    # CAN 버스 초기화
    can_bus = can.interface.Bus(
        bustype='socketcan',
        channel='can0',
        bitrate=500000
    )

    # 메인 설정
    SAVE_FLAG   = config['MEASUREMENT']
    DATASET_DIR = os.path.join(config['SAVE_PATH'], 'check_data')
    PRINT_STAT  = config['CAN']['print_can_status']

    # 사용할 DBC 파일명 (config나 인자로 변경 가능)
    dbc_file = 'hyundai_2015_ccan.dbc'  # 예: 'P_CAN.dbc', 'C_CAN.dbc', 'M_CAN.dbc' 등

    # 스레드 이벤트
    stop_evt = threading.Event()

    try:
        sniff_can_dbc(
            d_name='CAN',
            save_flag=SAVE_FLAG,
            dataset_path=DATASET_DIR,
            dbc_filename=dbc_file,
            can_bus=can_bus,
            print_status=PRINT_STAT,
            stop_event=stop_evt
        )
    except KeyboardInterrupt:
        stop_evt.set()
        print("[INFO] KeyboardInterrupt received. Exiting...")
