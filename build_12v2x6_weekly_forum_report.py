import calendar
import re
from collections import Counter
from datetime import date, datetime
from html import escape
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

BASE_DIR = Path(__file__).resolve().parent
REPORT_DIR = BASE_DIR / 'reports'
REPORT_DIR.mkdir(exist_ok=True)
GENERATED_AT = datetime.now().astimezone()
REPORT_DATE = GENERATED_AT.date()
OUTPUT_STAMP = GENERATED_AT.strftime('%Y-%m-%d_%H%M%S')
OUT = REPORT_DIR / f'12v2x6_gpu_protection_weekly_report_{OUTPUT_STAMP}.html'


def subtract_months(value, months):
    month_index = value.year * 12 + value.month - 1 - months
    year, month_zero = divmod(month_index, 12)
    month = month_zero + 1
    day = min(value.day, calendar.monthrange(year, month)[1])
    return value.replace(year=year, month=month, day=day)


def canonical_url(url):
    parts = urlsplit(url.strip())
    path = re.sub(r'/+$', '', parts.path)
    host = parts.netloc.lower()
    query_pairs = parse_qsl(parts.query, keep_blank_values=False)
    stable_query = []
    # NGA玩家社區 與部分 Discuz 論壇把文章 ID 放在 query；不能連同追蹤參數一起移除。
    if host in {'bbs.nga.cn', 'nga.178.com'} and path.endswith('/read.php'):
        stable_query = [(key.lower(), value) for key, value in query_pairs if key.lower() == 'tid']
    elif host.endswith('chiphell.com') and path.endswith('/forum.php'):
        stable_query = [(key.lower(), value) for key, value in query_pairs if key.lower() == 'tid']
    return urlunsplit((parts.scheme.lower(), host, path, urlencode(stable_query), ''))


def extract_detail_urls(report_path):
    try:
        text = report_path.read_text(encoding='utf-8')
    except (OSError, UnicodeError):
        return set()
    match = re.search(r'<table id="detailTable".*?</table>', text, flags=re.S)
    if not match:
        return set()
    return {
        canonical_url(url)
        for url in re.findall(r'<a href="([^"]+)"', match.group(0))
        if url.startswith(('http://', 'https://'))
    }


PERIOD_START = date(2025, 7, 1)
PERIOD_END = REPORT_DATE

rows = [
    {
        'date': '2026-07-16', 'source': 'Reddit', 'keyword': 'GPU Safeguard',
        'match': '內文＋留言',
        'title': 'MSI MPG Ai1600TS per-pin current monitoring — I reversed the USB protocol',
        'summary': '發文者為了解 MPG Ai1600TS 的 GPU Safeguard+ 監控內容，分析 PSU 的 USB HID 通訊，確認可讀取電壓、電流、效率、溫度、風扇轉速，以及兩組 12V-2x6 接頭共 12 個 pin 的逐 pin 電流；並公開 Python 工具，支援文字、JSON 與 Prometheus 輸出。主文也說明 Linux hidraw、systemd 定時收集及 Proxmox USB passthrough 的使用方式。',
        'comments': '一名 Ai1600TS 使用者表示目前透過 HWiNFO、Graphite 與 Grafana 取得資料，認為原生 Prometheus 輸出更合適並準備試用；Linux 使用者也肯定可用性。另有留言指出 MSI Afterburner PSU plugin／SDK 已公開部分協定，因此「逆向」說法有爭議；發文者與其他留言者則強調先前缺少可直接使用的 Linux 實作。這篇證明跨平台 telemetry 的需求與開源工具價值，但沒有測試保護觸發、降載或關機效果。',
        'url': 'https://www.reddit.com/r/MSI_Gaming/comments/1uxj6a2/msi_mpg_ai1600ts_perpin_current_monitoring_i/'
    },
    {
        'date': '2026-07-15', 'source': 'Reddit', 'keyword': 'GPU Safeguard',
        'match': '標題＋內文＋留言',
        'title': 'MSI MPG Ai1300TS — +12V wattage reading seems way off at idle',
        'summary': 'Ai1300TS 使用者看到主 +12V rail 約 23A／278W，但六個 12V-2x6 pin 合計約 3.2A／38W，因此懷疑低負載 telemetry 校準異常；他同時表示逐 pin GPU 讀值看起來合理，MSI Center 與 HWiNFO 顯示一致。',
        'comments': '留言指出主 +12V 電流還包含 CPU 與其他元件，不能只與 GPU 六個 pin 相加比較；另一名 Ai1600TS 使用者表示智慧插座與 PSU 總功耗只差約 5W。現有留言不支持「感測器已失準」的結論，但顯示介面需要清楚區分整機 rail 與 GPU connector，避免使用者誤判。',
        'url': 'https://www.reddit.com/r/MSI_Gaming/comments/1uwzpqn/msi_mpg_ai1300ts_12v_wattage_reading_seems_way/'
    },
    {
        'date': '2026-07-09', 'source': 'Reddit', 'keyword': 'GPU Safeguard',
        'match': '型號＋留言',
        'title': 'Avoid MSI AI1600TS if you when something silent',
        'summary': '發文者表示兩台 Ai1600TS 都在約 730–750W 以上出現明顯 coil whine，並準備退貨；收回包裝時又回報一條線從接頭脫落。這是兩台個人樣本，不能推論所有產品皆如此。',
        'comments': '另一名使用者表示自己的 Ai1600TS 在超過 1000W 時仍安靜，正反經驗並存。發文者因此表示會等待 Seasonic OptiGuard；MSI HQ 人員在留言中要求取回兩台裝置調查。此篇反映整合式保護 PSU 的噪音、線材組裝與競品轉換風險，未測試 Safeguard+ 是否觸發。',
        'url': 'https://www.reddit.com/r/MSI_Gaming/comments/1ur8ybe/avoid_msi_ai1600ts_if_you_when_something_silent/'
    },
    {
        'date': '2026-07-06', 'source': 'Reddit', 'keyword': 'GPU Safeguard',
        'match': '內文＋留言',
        'title': 'Need some Advise on the new MSI MPG Ai1300 TS',
        'summary': 'RTX 5090 使用者主要因 Safeguard+ 考慮購買 Ai1300TS，但找不到足夠評測，因此詢問是否值得購買或應等待更多實際案例。',
        'comments': '有人建議既有優質 PSU 搭配 WireView；發文者認為 Safeguard+ 可降功率，而 WireView 主要是告警。留言補充 Wired WireView 可連接電源按鈕關機，也有人表示尚未看到這類 12VHPWR 修正方案確實有效的證據。這篇反映購買者需要第三方實測與清楚的競品功能比較。',
        'url': 'https://www.reddit.com/r/buildapc/comments/1uoypxa/need_some_advise_on_the_new_msi_mpg_ai1300_ts/'
    },
    {
        'date': '2026-06-12', 'source': 'Reddit', 'keyword': 'GPU Safeguard',
        'match': '內文＋留言',
        'title': 'Review: MSI MPG Ai1600 TS PCIE5 PSU Review',
        'summary': '主文分享 Ai1600TS 外部評測；可見留言中，一名法國使用者實際安裝後肯定黃色 12V-2x6 線材的插入辨識與鎖定手感，但指出需使用 beta MSI Afterburner 才能取得 PSU plugin 與 Safeguard+ 軟體功能。',
        'comments': '留言者從 PSU.cfg 找到 MaxCurrent、CurrentDif 與 SoftwareAlarm 設定，並回報把門檻設為 7A 後出現警報、功率限制降到 75%；這是個人測試，不是預設門檻或獨立驗證。另有人希望縮短硬關機時間與降低硬體上限。頁面仍有 16 則折疊回覆本次未展開，因此摘要只代表已讀到的可見留言。',
        'url': 'https://www.reddit.com/r/MSI_Gaming/comments/1u3njt8/review_msi_mpg_ai1600_ts_pcie5_psu_review/'
    },
    {
        'date': '2026-06-08', 'source': 'TechPowerUp Forums', 'keyword': 'WireView',
        'title': 'Thermal Grizzly Shows New WireView Pro II Noctua Edition and New WireView II at Computex 2026',
        'summary': '主文說明 Pro II 可量測整個 12V-2x6 接頭及各 pin 的電壓、功率、溫度與電流；Noctua Edition 改用鋁殼、Noctua 風扇與半被動散熱，WireView II 則是同平台的較小版本、取消顯示器。主文寫明 Noctua Edition 預計 9 月上市且價格較高。',
        'comments': '留言確認它插在 GPU 端、電源線接到背面，也有人希望超過設定電流時能降功率或關機；另一則留言表示可由使用者設定 cutoff。留言同時質疑額外重量、接點數與插拔／機械應力造成的風險。',
        'url': 'https://www.techpowerup.com/forums/threads/thermal-grizzly-shows-new-wireview-pro-ii-noctua-edition-and-new-wireview-ii-at-computex-2026.349824/'
    },
    {
        'date': '2026-06-12', 'source': 'TechPowerUp Forums', 'keyword': 'WireView',
        'title': 'Close call... 5090 Burnt Cable — WireView Pro II / Ampinel 討論',
        'summary': '留言把 WireView Pro II 與 Ampinel 並列討論，焦點是 5090 線材熔損後的保護方式。',
        'comments': '留言者表示兩者都會在電源鏈增加一個故障點，也受插拔循環限制；這是該留言者的看法，並非主文測試結論。',
        'url': 'https://www.techpowerup.com/forums/threads/close-call-5090-burnt-cable.334508/post-5736651'
    },
    {
        'date': '2026-07-02', 'source': 'TechPowerUp Forums', 'keyword': 'WireView',
        'title': 'Close call... 5090 Burnt Cable — WireView Pro II 使用建議',
        'summary': '留言者分享 WireView Pro 2 的拆裝方式。',
        'comments': '留言建議需要拆裝時從 WireView 本體拔 PSU 線，不要反覆從 GPU 端拔出；理由是希望保護 GPU 與 WireView 端子。',
        'url': 'https://www.techpowerup.com/forums/threads/close-call-5090-burnt-cable.334508/post-5748182'
    },
    {
        'date': '2026-07-16', 'source': 'TechPowerUp Forums', 'keyword': 'WireView',
        'title': 'Close call... 5090 Burnt Cable — WireView 警報後的保固疑問',
        'summary': '留言者提到有人忽略 WireView Pro 的警告。',
        'comments': '留言詢問 Thermal Grizzly 是否會處理保固，並表示在該情境中 WireView 已完成它被設計來做的警告工作；同串另一位使用者則說自己的 5080 使用 WireView Pro 2 與 16AWG 線材，會持續觀察。',
        'url': 'https://www.techpowerup.com/forums/threads/close-call-5090-burnt-cable.334508/post-5755006'
    },
    {
        'date': '2026-07-29', 'source': 'TechPowerUp Forums', 'keyword': 'WireView',
        'title': 'Close call... 5090 Burnt Cable — WireView 主要是資訊監控工具的看法',
        'summary': '兩則留言討論 WireView 的使用意願與監控價值。',
        'comments': '一位留言者表示第一次 WireView 使用失敗，若再買會考慮有線版；另一位認為 WireView 主要提供資訊，pin 仍會隨時間劣化，HWiNFO64 加警報可完成相近監控。',
        'url': 'https://www.techpowerup.com/forums/threads/close-call-5090-burnt-cable.334508/post-5761950'
    },
    {
        'date': '2026-07-02', 'source': 'TechPowerUp Forums', 'keyword': 'GPU Safeguard',
        'title': 'MSI MPG Ai1600TS — safeguard tech 討論',
        'summary': '留言直接討論 safeguard tech 用於在系統嚴重故障前偵測問題。',
        'comments': '留言認為需要 safeguard tech 來偵測問題本身就很荒謬，並批評業界多年未妥善處理接頭設計。',
        'url': 'https://www.techpowerup.com/forums/threads/msi-mpg-ai1600ts.346215/post-5747971'
    },
    {
        'date': '2026-07-22', 'source': 'TechPowerUp Forums', 'keyword': 'OptiGuard',
        'title': 'Seasonic Prime TX-1600W Noctua Edition — OptiGuard 開發與競品失敗討論',
        'summary': '留言提到 Seasonic 網站仍標示 OptiGuard coming soon。',
        'comments': '留言將 OptiGuard 與 ASRock TempGuard 的競品失敗案例放在一起討論，並表示希望 Seasonic 確保不重演。',
        'url': 'https://www.techpowerup.com/forums/threads/seasonic-prime-tx-1600w-noctua-edition.349357/post-5758199'
    },
    {
        'date': '2026-07-22', 'source': 'TechPowerUp Forums', 'keyword': 'OptiGuard',
        'title': 'Seasonic Prime TX-1600W Noctua Edition — OptiGuard 尚未成為標準',
        'summary': '留言提到 OptiGuard 尚未成為標準，並與 Seasonic PSU 產品規劃一起討論。',
        'comments': '留言批評 Seasonic 優先處理尚未推出的 GPU 型號支援，卻還沒把 OptiGuard 做成標準。',
        'url': 'https://www.techpowerup.com/forums/threads/seasonic-prime-tx-1600w-noctua-edition.349357/post-5758206'
    },
    {
        'date': '2026-06-12', 'source': 'TechPowerUp Forums', 'keyword': 'Ampinel',
        'title': 'Close call... 5090 Burnt Cable — Ampinel 與 WireView 比較',
        'summary': '留言將 Ampinel 與 WireView Pro II 並列為 5090 線材保護產品。',
        'comments': '留言指出 WireView 或 Ampinel 會增加一個故障點，且同樣受到插拔循環壽命限制。',
        'url': 'https://www.techpowerup.com/forums/threads/close-call-5090-burnt-cable.334508/post-5736530'
    },
    {
        'date': '2026-06-01', 'source': 'TechPowerUp Forums', 'keyword': 'ROG Equalizer',
        'title': 'ASUS Now Bundles ROG Equalizer Cable with Thor III, Strix Platinum PSUs',
        'summary': '主題介紹 Thor III 與 Strix Platinum 電源供應器開始隨附 ROG Equalizer 12V-2x6 PCIe 電源線，搜尋結果摘要提到 17A peak capacity。',
        'comments': '留言對 ROG Equalizer 的接觸設計、金屬鍍層與是否真正改善長期可靠性有正反意見。',
        'url': 'https://www.techpowerup.com/forums/threads/asus-now-bundles-rog-equalizer-cable-with-thor-iii-strix-platinum-psus.349555/'
    },
    {
        'date': '2026-06-15', 'source': 'TechPowerUp Forums', 'keyword': 'ROG Equalizer',
        'title': 'ASUS Introduces ROG Equalizer 12V-2x6 Cable for GPU Power Stability',
        'summary': '留言引用 ROG Equalizer 的 4-spring contacts 與 GPU 端 busbar，說明其理論上可把各線形成平行供電面、降低單 pin 過載機率；同一留言也明確表示仍可能過載。',
        'comments': '留言認為若把 PSU 端也加上對應 busbar，設計可能更完整；並把 ThermalProtect、ROG Equalizer、Titanload 都描述為緩解方案而非根治方案。另一位留言者則直接批評 ASUS 線材不能主動控制電流分配。',
        'url': 'https://www.techpowerup.com/forums/threads/asus-introduces-rog-equalizer-12v-2x6-cable-for-gpu-power-stability.348123/post-5738904'
    },
      {
        'date': '2026-07-19', 'source': 'TechPowerUp Forums', 'keyword': 'ROG Equalizer',
        'title': 'Close call... 5090 Burnt Cable — ROG Equalizer 到貨',
        'summary': '留言提到使用者收到 ROG Equalizer。',
        'comments': '留言表示白色版本較容易從外觀察覺變色或熔化，並將顏色選擇描述為外觀考量。',
        'url': 'https://www.techpowerup.com/forums/threads/close-call-5090-burnt-cable.334508/post-5756316'
      },
      {
        'date': '2026-06-01', 'source': 'TechPowerUp Forums', 'keyword': 'Titanload',
        'title': 'ASUS Now Bundles ROG Equalizer Cable with Thor III, Strix Platinum PSUs — Titanload 比較',
        'summary': '留言將 Segotep Titanload 與 ROG Equalizer 比較，討論接點強度與長期接觸。',
        'comments': '一位留言者認為 Titanload 的 pin 內部接觸更強；另一位指出 ASUS 使用 4-spring contact、較大接觸面積，並表示找不到足夠的 Titanload 英文資料。',
        'url': 'https://www.techpowerup.com/forums/threads/asus-now-bundles-rog-equalizer-cable-with-thor-iii-strix-platinum-psus.349555/post-5731303'
      },
    {
        'date': '2026-06-13', 'source': 'TechPowerUp Forums', 'keyword': 'ThermalProtect',
        'title': 'Close call... 5090 Burnt Cable — Corsair ThermalProtect 與 ROG Equalizer',
        'summary': '留言討論 Corsair ThermalProtect 與 ASUS ROG Equalizer 在 5080/5090 線材保護上的取捨。',
        'comments': '留言表示即使 RTX 5080 功耗低於 4090/5090，仍考慮購買 ThermalProtect；同時認為 ROG Equalizer 的方向也有吸引力。',
        'url': 'https://www.techpowerup.com/forums/threads/close-call-5090-burnt-cable.334508/post-5737373'
    },
    {
        'date': '2026-07-13', 'source': 'TechPowerUp Forums', 'keyword': 'ThermalProtect',
        'title': 'Close call... 5090 Burnt Cable — ThermalProtect 疑似避免第二次熔損',
        'summary': '留言者描述在約 400W 持續負載遊玩 Star Rail 約兩小時後，系統自行關機。',
        'comments': '留言者寫的是「可能」因此避免第二次熔損，並說含稅運費約 41 美元已值得；另一位留言者稱這是 hard shutdown。這是使用者個案，不能推成普遍效果。',
        'url': 'https://www.techpowerup.com/forums/threads/close-call-5090-burnt-cable.334508/post-5753286'
    },
    {
        'date': '2026-06-20', 'source': 'TechPowerUp Forums', 'keyword': 'ThermalProtect',
        'title': 'Power Supply for my build — Corsair ThermalProtect',
        'summary': '留言建議 5090 使用 Corsair ThermalProtect 線材，並附上產品連結。',
        'comments': '留言明確表示該線材可搭配具有原生 12VHPWR 插座的 PSU。',
        'url': 'https://www.techpowerup.com/forums/threads/power-supply-for-my-build.350107/post-5740991'
    },
    {
        'date': '2026-07-11', 'source': 'TechPowerUp Forums', 'keyword': 'TempGuard',
        'title': 'Close call... 5090 Burnt Cable — ASRock TempGuard 失效案例',
        'summary': '留言描述 ASRock safety cable 兩側失效，PSU 側發生嚴重熔損；ASRock Phantom Gaming 1000W PSU 受損送回。',
        'comments': '同串留言指出 MSI Gaming Trio 5090 只出現輕微受損，但這是特定個案的論壇敘述。',
        'url': 'https://www.techpowerup.com/forums/threads/close-call-5090-burnt-cable.334508/post-5752634'
    },
    {
        'date': '2026-07-11', 'source': 'TechPowerUp Forums', 'keyword': 'TempGuard',
        'title': 'Close call... 5090 Burnt Cable — TempGuard 與 ThermalProtect 架構差異',
        'summary': '留言比較 ASRock TempGuard 與 Corsair ThermalProtect 的感測位置。',
        'comments': '留言指出 TempGuard 探頭位於 PSU 專用端子、靠近熔損處；Corsair ThermalProtect 則採 inline 方式，並宣稱可跨 PSU 使用。',
        'url': 'https://www.techpowerup.com/forums/threads/close-call-5090-burnt-cable.334508/post-5752674'
    },
    {
        'date': '2026-06-02', 'source': "Tom's Hardware Forums", 'keyword': 'GPU Shield',
        'title': 'Cooler Master shows off new MWE Gold V4 Power supplies and GPU Shield adapter — per-pin monitoring can dynamically scale down power to stop cables...',
        'summary': '搜尋結果頁與主題首文提到 Cooler Master 在 Computex 展示 MWE Gold V4 電源供應器與 GPU Shield adapter；頁面文字指出 GPU Shield 採 per-pin monitoring，並可動態降低功率以避免線材問題。',
        'comments': '可讀到 4 則回覆。其中一則認為廠商不應替 PCI-SIG/Nvidia 的規格問題善後；另一則表示 12VHPWR/2x6 的缺陷催生了保護產品市場，使用者可能願意購買 100–300 美元的 PSU 來保護高價顯示卡。',
        'url': 'https://forums.tomshardware.com/threads/cooler-master-shows-off-new-mwe-gold-v4-power-supplies-and-gpu-shield-adapter-%E2%80%94-per-pin-monitoring-can-dynamically-scale-down-power-to-stop-cables.3896668/'
    },
    {
        'date': '2026-07-12', 'source': "Tom's Hardware Forums", 'keyword': 'GPU Shield',
        'title': 'Cooler Master MWE Gold 750 V4 power supply review: Verified Gold efficiency with mainstream pricing',
        'summary': '搜尋結果頁與主題首文提到該電源供應器具備原生 12V-2x6 接頭，以及 GPU Shield current monitoring；主題頁未顯示使用者回覆。',
        'comments': '未讀到使用者留言內容；頁面顯示回覆數為 0。',
        'url': 'https://forums.tomshardware.com/threads/cooler-master-mwe-gold-750-v4-power-supply-review-verified-gold-efficiency-with-mainstream-pricing.3897955/'
    },
    {
        'date': '2026-07-30', 'source': 'TechPowerUp Forums', 'keyword': 'Ampinel', 'match': '留言',
        'title': 'Close call... 5090 Burnt Cable',
        'summary': '第 586 則留言彙整近期熔損案例，其中一例描述 Ampinel 本體熔損，並表示 GPU 據報仍存活。',
        'comments': '實際頁面只讀到該留言對外部案例的簡述，沒有 Ampinel 使用者本人提供的負載、接線、警報或保護過程；因此只能確認「論壇轉述一件熔損案例」，不能判定原因或普遍失效率。',
        'url': 'https://www.techpowerup.com/forums/threads/close-call-5090-burnt-cable.334508/post-5762386'
    },
    {
        'date': '2026-07-27', 'source': 'TechPowerUp Forums', 'keyword': 'ROG Equalizer', 'match': '留言',
        'title': 'Close call... 5090 Burnt Cable',
        'summary': '連續留言討論 ROG Equalizer 是否可跨品牌 PSU 使用、是否真的主動均流，以及金鍍層與 GPU 端不同金屬接點的長期問題。',
        'comments': '一位實際購買者表示可搭配非 ASUS PSU，但也明確說 Equalizer 不做主動電流平衡；另一位質疑保固、鍍層厚度、塑膠耐熱及接點仍是瓶頸。後續留言認為 5090 使用可能有價值，但價格效益仍可疑。',
        'url': 'https://www.techpowerup.com/forums/threads/close-call-5090-burnt-cable.334508/post-5760564'
    },
    {
        'date': '2026-07-25', 'source': 'TechPowerUp Forums', 'keyword': 'ThermalProtect', 'match': '留言',
        'title': 'Close call... 5090 Burnt Cable',
        'summary': '留言把 WireView、ROG Equalizer 與 Thermal Protect 視為額外購買的安全保險。',
        'comments': '使用者估算若現有 PSU 不相容或需要更換配套，總成本可能上升到約 150 美元，並批評這像是向仍使用 12V-2x6 的使用者收取額外安全成本；這是個人估算，不是產品定價表。',
        'url': 'https://www.techpowerup.com/forums/threads/close-call-5090-burnt-cable.334508/post-5760028'
    },
    {
        'date': '2026-07-05', 'source': 'TechPowerUp Forums', 'keyword': 'GPU Safeguard', 'match': '留言',
        'title': 'MSI MPG Ai1600TS',
        'summary': '完整主題包含產品評測摘要與 13 則近期留言；使用者把 Safeguard+ 視為購買 1600W 型號及雙高階 GPU 配置的主要理由。',
        'comments': '肯定面包括 current monitoring、12 年保固及功能完整；批評集中在價格過高、歐洲供貨、Windows／MSI Center 鎖定、USB 安全與效率、量測精度未公布，以及故障後仍需開機才能讀取記錄。另有留言希望功能下放到約 1000W／250 美元級距，並指出 A-PLS 系列可提供不含軟體的版本。',
        'url': 'https://www.techpowerup.com/forums/threads/msi-mpg-ai1600ts.346215/'
    },
    {
        'date': '2026-06-08', 'source': 'TechPowerUp Forums', 'keyword': 'GPU Shield', 'match': '內文＋留言',
        'title': 'Cooler Master Launches MWE Gold V4 Series with GPU Shield',
        'summary': '主文說明 GPU Shield 偵測異常電流、即時主動保護與 LED 警示；本次重新讀取主文及全部 7 則留言。',
        'comments': '留言普遍把 GPU Shield 視為 12V-2x6 接頭缺陷衍生的補救方案，而非根因修正。有人比較 MSI Safeguard+、ASRock、Ampinel、WireView 與 ThermalProtect，認為 MSI 方案較有可信度、ThermalProtect 簡單便宜但不完整；也指出 Ampinel 昂貴、缺貨且均流功能具爭議。',
        'url': 'https://www.techpowerup.com/forums/threads/cooler-master-launches-mwe-gold-v4-series-with-gpu-shield.349823/'
    },
    {
        'date': '2026-07-20', 'source': 'Reddit', 'keyword': 'WireView', 'match': '內文＋留言',
        'title': 'Just got the WireView Pro II and immediately got a Current Imbalance error. How do I proceed?',
        'summary': '發文者安裝後立即看到 Line 5／6 電流異常，測試約 450W 遊戲後停止使用；檢查接頭外觀未見損傷。',
        'comments': '留言建議檢查 GPU、PSU 與 WireView 三端是否完全插入，並發現照片中有退縮的 pins；更換 PSU 線材後六路讀值恢復一致。這是一個由告警導向排除線材問題的成功個案。',
        'url': 'https://www.reddit.com/r/ThermalGrizzly/comments/1v1r6oc/just_got_the_wireview_pro_ii_and_immediately_got/'
    },
    {
        'date': '2026-07-20', 'source': 'Reddit', 'keyword': 'WireView', 'match': '內文＋留言',
        'title': 'Just installed my new Wireview Pro II wired',
        'summary': 'Gigabyte RTX 5070 Ti 的接頭位置太深入散熱器，普通版無法安裝；發文者改用 Wired 版與 GPU screw holes／bracket 完成安裝。',
        'comments': '留言質疑 5070 Ti 是否需要此保護；使用者表示雖然風險可能低，但因顯示卡約 1000 美元且不信任便宜 90 度轉接頭，仍願意支付約 170 美元。安裝順序、支架與螺絲適配是主要資訊需求。',
        'url': 'https://www.reddit.com/r/ThermalGrizzly/comments/1v1jb4z/just_installed_my_new_wireview_pro_ii_wired/'
    },
    {
        'date': '2026-07-19', 'source': 'Reddit', 'keyword': 'WireView', 'match': '內文＋留言',
        'title': 'Wire View 2 Software causes huge Performance Impact ~30% even running it in Tray!',
        'summary': '發文者表示 WireView Pro II 軟體常駐系統列時，VR 模擬賽車約損失 30% FPS；關閉軟體後恢復。',
        'comments': '另一位 5090 使用者也回報功耗由約 575W 降至 450W且分數下降，關閉軟體後正常。官方回覆 1.0.7 已降低負載、軟體只需設定時使用，裝置可獨立運作；仍有使用者要求明顯警告、輕量背景版及改善斷線。',
        'url': 'https://www.reddit.com/r/ThermalGrizzly/comments/1v0uzle/wire_view_2_software_causes_huge_performance/'
    },
    {
        'date': '2026-07-19', 'source': 'Reddit', 'keyword': 'WireView', 'match': '留言',
        'title': 'Bad plastic injection or potential melting?',
        'summary': '5090 TUF 使用一年後，發文者在清潔時發現 12VHPWR pins 形狀異常，詢問是射出成形問題或熔化。',
        'comments': '多則留言判斷可能已熔化，建議更換或維修接頭；有人建議 WireView 或 Corsair ThermalProtect，也有人因此拒絕升級到使用此接頭的 GPU。無法僅憑論壇照片確認實際損壞原因。',
        'url': 'https://www.reddit.com/r/pcmasterrace/comments/1v120m6/bad_plastic_injection_or_potential_melting/'
    },
    {
        'date': '2026-07-17', 'source': 'Reddit', 'keyword': 'WireView', 'match': '內文＋留言',
        'title': 'WireView Pro 2 Wired Mounting Screws',
        'summary': '發文者詢問 Wired 版是否附 mounting screws。',
        'comments': '已讀資料顯示留言回覆有附螺絲，但長度不長；反映包裝內容與不同 GPU／支架的適配資訊需要更清楚。',
        'url': 'https://www.reddit.com/r/ThermalGrizzly/comments/1uz6iiy/wireview_pro_2_wired_mounting_screws/'
    },
    {
        'date': '2026-07-16', 'source': 'Reddit', 'keyword': 'WireView', 'match': '內文＋留言',
        'title': 'WireView Pro II Wired on RTX Pro 6000 - finally the GPU is safe',
        'summary': 'RTX Pro 6000 使用者在 AI inference 超過 600W 的情境安裝 Wired 版並測試 over-current shutdown，表示因此敢讓系統無人看管運作。',
        'comments': '留言質疑兩個 pin 到 9A 仍不安全並建議限制 450–500W；討論確認 WireView 可自動關機但不做 Ampinel 式均流，且會增加一個 12V-2x6 連接點。使用者把「監控＋斷電」視為 Ampinel 缺貨時的可用替代方案。',
        'url': 'https://www.reddit.com/r/ThermalGrizzly/comments/1uy826k/wireview_pro_ii_wired_on_rtx_pro_6000_finally_the/'
    },
    {
        'date': '2026-07-16', 'source': 'Reddit', 'keyword': 'GPU Safeguard', 'match': '留言',
        'title': 'RTX Pro 6000 with Thermal Grizzly WireView Pro II Wired-edition',
        'summary': '主文完整說明 Wired 版接線、Y-cable 關機、兩支熱電偶與 USB 遙測。',
        'comments': '留言把具有 GPU per-pin over-current protection 的 MSI MPG Ai1600TS 列為替代方案；另有使用者在 WireView Wired 與 Ampinel 間猶豫，並擔心關機後無法立刻分辨是停電、誤報或 GPU 故障。',
        'url': 'https://www.reddit.com/r/nvidia/comments/1uy88v8/rtx_pro_6000_with_thermal_grizzly_wireview_pro_ii/'
    },
    {
        'date': '2026-07-15', 'source': 'Reddit', 'keyword': 'WireView', 'match': '內文＋留言',
        'title': 'WireView Pro melted on my Gigabyte AORUS RTX 5090 Xtreme Waterforce',
        'summary': '發文者描述 WireView Pro 多次告警後，雖曾降到 90% power limit，最終裝置仍部分熔化。',
        'comments': '留言批評忽略告警，也追問突然 imbalance 後究竟應送修 GPU、PSU 或換線。有人分享換線後告警消失，並建議告警後立即限功率、檢查兩端與更換線材；另有留言比較 ThermalProtect、TempGuard、Equalizer 與 WireView 的不同保護邏輯。',
        'url': 'https://www.reddit.com/r/ThermalGrizzly/comments/1uxhwl3/wireview_pro_melted_on_my_gigabyte_aorus_rtx_5090/'
    },
    {
        'date': '2026-07-11', 'source': 'Reddit', 'keyword': 'TempGuard', 'match': '標題＋留言',
        'title': 'ASRock TempGuard failed to shut down system after RTX 5090 power connector melted',
        'summary': '主文為外部報導連結；可讀價值主要來自留言對保護失效與替代方案的討論。',
        'comments': '留言指出 thermistor 可能位在接頭錯側，導致接頭受損後才反應；有人建議 ThermalProtect，也有人主張使用 Safeguard+ 限制每 pin 9.0A、imbalance 1A，並在約 3 秒內載入降功率設定。各方案效果仍有爭論。',
        'url': 'https://www.reddit.com/r/ASRock/comments/1utcp5x/asrock_tempguard_failed_to_shut_down_system_after/'
    },
    {
        'date': '2026-07-11', 'source': 'Reddit', 'keyword': 'GPU Safeguard', 'match': '留言',
        'title': 'ASRock TempGuard failed to shut down system after RTX 5090 power connector melted',
        'summary': '文章標題是 TempGuard 失效案例，但留言詳細討論 MSI Safeguard+ 的 per-pin 門檻與自動降載。',
        'comments': '一位使用者表示可設定每 pin 9.0A、pin 差異 1A，約 3 秒後由 Afterburner 載入 profile，將約 9A 以上降到 4–6A；這是單一使用者敘述，非本次獨立測試。',
        'url': 'https://www.reddit.com/r/pcmasterrace/comments/1utff9u/asrock_tempguard_failed_to_shut_down_system_after/'
    },
    {
        'date': '2026-07-10', 'source': 'Reddit', 'keyword': 'GPU Safeguard', 'match': '留言',
        'title': "It's just comical at this point.",
        'summary': '主文連到 TempGuard 失效報導，標題沒有任何指定產品名稱。',
        'comments': '留言明確提到 Safeguard+、WireView Pro II、ThermalProtect 等方案，並主張 active pin monitoring 與 automatic shutdown；同時認為即使使用彩色接頭、專用 PSU 與保護線仍可能失效，根因是接頭設計。',
        'url': 'https://www.reddit.com/r/pcmasterrace/comments/1uszwr7/its_just_comical_at_this_point/'
    },
    {
        'date': '2026-07-10', 'source': 'Reddit', 'keyword': 'Ampinel', 'match': '留言',
        'title': 'Avoid 12vhpwr melting?',
        'summary': '5090 使用者詢問在約 330W undervolt 之外，還能如何降低線材熔毀風險；標題沒有 Ampinel 或 WireView。',
        'comments': '留言比較 WireView Pro II 與 Ampinel：前者可監控並經主機板開關接線在危險電流時關機，後者嘗試平衡六路 12V 電流；留言也指出均流仍是補丁，無法修復鬆動或高阻抗接點。',
        'url': 'https://www.reddit.com/r/pcmasterrace/comments/1ust8i0/avoid_12vhpwr_melting/'
    },
    {
        'date': '2026-07-07', 'source': 'Reddit', 'keyword': 'GPU Safeguard', 'match': '標題＋內文',
        'title': 'MSI PSU safeguard+ custom amp limits guide',
        'summary': '使用者整理 Ai1600TS／Ai1300TS 的 Safeguard+ 設定欄位：currentmax 為單 pin 最大電流，currentdif 為 pin 間允許差異。',
        'comments': '讀取時未見可用留言；只能確認使用者需要清楚的門檻欄位與官方建議值，不能據此判定設定成效。',
        'url': 'https://www.reddit.com/r/MSI_Gaming/comments/1upfvw4/msi_psu_safeguard_custom_amp_limits_guide/'
    },
    {
        'date': '2026-07-05', 'source': 'Reddit', 'keyword': 'ThermalProtect', 'match': '內文＋留言',
        'title': 'Installed Wire View pro II and Corsair thermal protect cable on my RTX 5090, no more melting anxiety',
        'summary': '發文者在 RTX 5090 同時安裝 WireView Pro II 與 Corsair ThermalProtect cable，表示降低了熔損焦慮。',
        'comments': '留言爭論 WireView 介入後 ThermalProtect 的感測位置與保護是否仍有效；有人嫌 WireView 價格高而偏好 PSU 內建保護，也有人比較 Safeguard+、OptiGuard、Ampinel 與 Equalizer。這反映多層防護的監控邊界缺乏清楚說明。',
        'url': 'https://www.reddit.com/r/nvidia/comments/1uoepk0/installed_wire_view_pro_ii_and_corsair_thermal/'
    },
    {
        'date': '2026-07-04', 'source': 'Reddit', 'keyword': 'Ampinel', 'match': '內文＋留言',
        'title': 'Questions About 12V-2x6 Connector Wear and Cable Selection',
        'summary': '發文者詢問 RTX 5090 多次插拔、Ampinel、ROG Equalizer 與線材選擇。',
        'comments': '留言建議避免反覆插拔；有人認為 Ampinel 能做 load balance，但若接點鬆動或高接觸電阻，均流不等於修復實體接觸。另有人建議 Safeguard+ 設 per-pin／current difference 門檻並觸發降載或關機。',
        'url': 'https://www.reddit.com/r/overclocking/comments/1umu2yx/questions_about_12v2x6_connector_wear_and_cable/'
    },
    {
        'date': '2026-07-04', 'source': 'Reddit', 'keyword': 'WireView', 'match': '留言',
        'title': 'It really can happen to you too!',
        'summary': '主文描述 Gigabyte OC RTX 4090 電源接頭燒毀，標題沒有指定產品名稱。',
        'comments': '留言把 WireView、Ampinel、MSI per-pin PSU 與 ThermalProtect 列為降低風險的方法；有使用者描述自己同時使用 per-pin current detection、over-current alert、automatic shutdown 與 ThermalProtect，呈現使用者偏好多層保護。',
        'url': 'https://www.reddit.com/r/pcmasterrace/comments/1unjyw4/it_really_can_happen_to_you_too/'
    },
    {
        'date': '2026-07-02', 'source': 'Reddit', 'keyword': 'WireView', 'match': '留言',
        'title': "Is it weird that I can afford an RTX 5090 but I'm not buying it purely out of fear that it will burn?",
        'summary': '發文者因 12V-2x6 熔損焦慮而猶豫是否購買 RTX 5090；標題沒有 WireView。',
        'comments': '留言建議 WireView Pro II，理由是可觀察高負載、警報及自動關機；也有人認為應改用不採此接頭的 GPU。使用者把監控裝置視為降低購買焦慮的條件，而非完全解決方案。',
        'url': 'https://www.reddit.com/r/pcmasterrace/comments/1ulyjce/is_it_werid_that_i_can_afford_an_rtx_5090_but_im/'
    },
    {
        'date': '2026-07-01', 'source': 'Reddit', 'keyword': 'ROG Equalizer', 'match': '標題＋內文＋留言',
        'title': "I've seen reports of the ASUS ROG Equalizer cable burning. Should I cancel my order?",
        'summary': '發文者已訂購 ROG Equalizer，但因看到 burning／overheating 報告而詢問是否取消。',
        'comments': '留言建議改選 WireView Pro II 或具 pin monitoring 的 PSU，也提到 ThermalProtect；同時提醒 Equalizer 不是萬靈丹，且網路燒痕圖片與測試證據真偽需要區分。',
        'url': 'https://www.reddit.com/r/ASUSROG/comments/1uktwty/ive_seen_reports_of_the_asus_rog_equalizer_cable/'
    },
    {
        'date': '2026-07-23', 'source': 'Reddit', 'keyword': 'WireView',
        'keywords': ['WireView', 'Ampinel', 'ROG Equalizer', 'ThermalProtect', 'GPU Safeguard'],
        'match': '留言',
        'title': '12V-2x6 connector and overthinking issues.',
        'summary': '發文者表示已確認 12V-2x6 完全插入，仍擔心 RTX 5080 接頭風險；標題與主文沒有列出保護產品名稱。',
        'comments': '留言直接比較 WireView Pro II、Ampinel、ROG Equalizer 搭配 PSU pin monitoring、CORSAIR ThermalProtect 與 MSI Safeguard+。留言者認為 ThermalProtect 在簡單、價格與安裝便利性上較有優勢；WireView 偏向監控，Wired 版可硬關機；Equalizer 搭配 PSU pin monitoring 是另一種組合，但沒有一致認定的最佳方案，且多裝置串接相容性仍不明確。',
        'url': 'https://www.reddit.com/r/RTX5080/comments/1v4gij1/12v2x6_connector_and_overthinking_issues/'
    },
    {
        'date': '2026-06-27', 'source': 'Reddit', 'keyword': 'WireView',
        'match': '標題＋內文＋留言',
        'title': 'WireView Pro II was worth it just for the peace of mind',
        'summary': '使用者實際安裝 WireView Pro II，肯定逐 pin 電流、電壓、溫度、警報、記錄與自動關機功能，也認為機構做工扎實；但因顯示卡與機殼空間不足，最後必須更換整個機殼，且明確表示裝置仍不能保證完全不會故障。',
        'comments': '可見留言很少；一則留言以「為了 OCD 換機殼」回應安裝成本，沒有提供額外技術驗證。',
        'url': 'https://www.reddit.com/r/pcmasterrace/comments/1uhce46/wireview_pro_ii_was_worth_it_just_for_the_peace/'
    },
    {
        'date': '2026-06-09', 'source': 'Reddit', 'keyword': 'WireView',
        'keywords': ['WireView', 'ThermalProtect', 'ROG Equalizer'],
        'match': '內文＋留言',
        'title': '12V 2x6 Bend',
        'summary': '發文者原本擔心 12V-2x6 彎折；更新內容表示已購買 WireView Pro II，安裝後沒有線材彎折，並可查看逐 pin 電流與總功率。',
        'comments': '留言討論機殼空間與彎折半徑，並有人表示正在 ThermalProtect 與 ROG Equalizer 間考慮；未提供兩者的實測比較。',
        'url': 'https://www.reddit.com/r/pcmasterrace/comments/1u0twhu/12v_2x6_bend/'
    },
    {
        'date': '2026-05-31', 'source': 'Reddit', 'keyword': 'WireView',
        'match': '標題＋內文＋留言',
        'title': 'WireView Pro II w/ 5090 current imbalance limits',
        'summary': '使用者在 RTX 5090 上看到 WireView Pro II 的第 6 pin 瞬間達 10.3A，詢問是否安全及應如何設定電流不平衡門檻。',
        'comments': '留言意見分歧：有人建議重插或更換線材，有人區分瞬間尖峰與持續高電流並建議降壓。發文者補充，使用 WireView 後共有三個 12V-2x6 介面與 18 個正極接點，任一接點都可能造成不平衡；本串沒有形成一致安全門檻。',
        'url': 'https://www.reddit.com/r/ThermalGrizzly/comments/1tt727g/wireview_pro_ii_w_5090_current_imbalance_limits/'
    },
]

# 2026 年初至原兩個月版本起點前，逐篇核讀後補入的有效討論。
rows.extend([
    # 2026-08-26 weekly refresh: each entry below was read from the visible post and comments.
    {
        'date': '2026-08-25', 'source': 'Reddit', 'keyword': 'WireView', 'match': '標題＋內文＋留言',
        'title': 'WireView Pro II 與 AIDA64 隨機斷線',
        'summary': 'RTX 5090 使用者搭配 WigiDash 與 AIDA64，表示 WireView 約使用三個月後會在桌面或遊戲中隨機從 AIDA64 與 Thermal Grizzly 軟體斷線；重啟 AIDA64 可暫時恢復。裝置本身的螢幕仍會顯示各 pin 功耗。',
        'comments': '頁面可見範圍沒有留言，也沒有錯誤紀錄或後續診斷；不能判定是 AIDA64、WireView 的 USB／韌體、或其他軟體造成。',
        'url': 'https://www.reddit.com/r/ThermalGrizzly/comments/1vy0wa9/wireview_pro_ii_get_disconnected_by_aida64/'
    },
    {
        'date': '2026-08-25', 'source': 'Reddit', 'keyword': 'WireView', 'match': '標題＋內文＋留言',
        'title': 'Wired WireView Pro II 重載時的 pin 電流差詢問',
        'summary': 'Founders Edition RTX 5090 使用者以 0.9V／2800MHz 輕度降壓、100% 功耗上限跑重度 AI 工作時，詢問中央 pin 電流較低是否正常。',
        'comments': '留言者把約 1.3A 差、各 pin 未超過 9.5A 視為可接受；另有 5090 使用者分享 15 分鐘 Cinebench＋FurMark 測試後詢問讀值，但可見文字沒有完整原始數據。接近 9A 時有人建議檢查插接與線材；這些都是論壇意見，非統一門檻或受控驗證。',
        'url': 'https://www.reddit.com/r/ThermalGrizzly/comments/1vxwevl/wired_wireview_pro_2_balance/'
    },
    {
        'date': '2026-08-25', 'source': 'Reddit', 'keyword': 'WireView', 'match': '標題＋內文＋留言',
        'title': 'WireView Pro II 預設門檻與自訂設定詢問',
        'summary': 'RTX 5090 使用者更新至最新韌體後，認為每 pin 約 10.5A 才通知的設定偏高；他表示原本 ASUS Astral 線材最高約 9.2A，遊戲時也觀察到裝置風扇約 10% 轉速。',
        'comments': '可見回覆分別主張維持預設，或自行設為 60°C、關機等待 0 秒與風扇 100%，另有人採 9.5A 與 soft shutdown。這些是個人設定，貼文沒有把它們證實為官方建議或保護效果測試。',
        'url': 'https://www.reddit.com/r/ThermalGrizzly/comments/1vxia5q/wirepro_2_default_settings_or_customize/'
    },
    {
        'date': '2026-08-23', 'source': 'Reddit', 'keyword': 'WireView', 'match': '標題＋內文＋留言',
        'title': 'WireView Pro II 是否有熔損接點案例的討論',
        'summary': '一名 WireView Pro II 擁有者表示裝置運作良好，詢問是否已知有接頭熔損案例；他自己僅使用約六個月、只遇過一次失衡告警，並說尚未真正遇到需要保護的情況。',
        'comments': 'Thermal Grizzly 論壇代表在此串表示，依其掌握回報，目前沒有 WireView Pro II 接頭熔損案例，並澄清被提及的熔損是第一代 WireView Pro；這是廠商陳述，不是獨立統計或故障注入測試。一名留言者稱裝置曾讓他淘汰兩條異常線材，另有使用者討論 Wired 版空間、外接探頭與自訂告警，均屬個案或使用建議。',
        'url': 'https://www.reddit.com/r/ThermalGrizzly/comments/1vvxc1d/curious_has_there_been_any_melted_cables_with_wvp2/'
    },
    {
        'date': '2026-08-22', 'source': 'Reddit', 'keyword': 'WireView', 'match': '標題＋內文＋留言',
        'title': 'Wired WireView Pro II 的 pin 1 偏高詢問',
        'summary': 'HX1500i、RTX 5090 Vanguard SOC 與 WireView Pro II Wired 使用者表示 pin 1 有時會比其他 pin 高約 1.5A，但從未超過 10A，因此詢問是否需要更換新線材。',
        'comments': '部分留言把約 1.4A 差與 FurMark 結果視為可接受；另一則建議反覆插拔以檢查接觸狀況，隨即有留言反對把更多插拔當作一般作法。後續澄清該說法是針對既有失衡的故障檢查，而非新線材的例行「磨合」。討論沒有診斷出根因。',
        'url': 'https://www.reddit.com/r/ThermalGrizzly/comments/1vvefxt/pin_1_imbalance/'
    },
    {
        'date': '2026-08-22', 'source': 'Reddit', 'keyword': 'WireView', 'match': '內文＋留言',
        'title': 'WireView 在 Linux 以 StreamController 呈現',
        'summary': '貼文展示 WireView 與 StreamController 的儀表板畫面；可見內容沒有安全事件或保護觸發測試。',
        'comments': '留言說明使用的是非官方 WireView Linux build、StreamController 與 hwmon 感測器；移植者表示已完成 Linux port，另有使用者把此整合視為使用 Linux 的重要條件。這可支持跨平台可視化需求，不能推論官方支援範圍或保護可靠性。',
        'url': 'https://www.reddit.com/r/ThermalGrizzly/comments/1vv6ckn/wireview_on_linux_using_streamcontroller/'
    },
    {
        'date': '2026-08-21', 'source': 'Reddit', 'keyword': 'WireView', 'match': '標題＋內文＋留言',
        'title': 'Starfield 中 WireView Pro II 告警與 pin 波動',
        'summary': 'RTX 5090 Starfield 使用者表示，即使 NVIDIA 功耗限制設為 80%，移動遊戲鏡頭時部分 pin 會由約 4A 跳到超過 9A、GPU 功耗短暫超過 575W；鏡頭靜止後讀值恢復。100% 功耗下跑 Steel Nomad 約 580W 時，他反而認為各 pin 均勻。',
        'comments': '留言把現象歸因於遊戲負載、V-Sync／Reflex、FPS 上限或 ERP BIOS 等可能性；發文者說其他遊戲較均衡，並考慮再測 ERP。沒有一致診斷或重現測試，不能把這些設定視為已證實根因。',
        'url': 'https://www.reddit.com/r/ThermalGrizzly/comments/1vug9an/probl%C3%A8me_r%C3%A9partition_broches/'
    },
    {
        'date': '2026-08-20', 'source': 'TechPowerUp Forums', 'keyword': 'ROG Equalizer', 'match': '內文＋留言',
        'title': '5090 線材討論中的 ThermalProtect 與 ASUS ROG Equalizer 實測比較',
        'summary': '一名水冷 RTX 5090 使用者表示，在低風扇轉速下，兩條 ThermalProtect 線材均能重現觸發；他也說接頭上的 10K 溫度感測器約 65°C、WireView Pro 約 600W 時可見此溫度。相同系統以 600W FurMark 跑一小時後，他稱 ASUS ROG Equalizer 保持冷卻、橋接處感覺最熱。',
        'comments': '回覆一方面質疑 ThermalProtect 在一般低風量使用可能觸發，另一方面肯定它在描述情境下已作動；對 Equalizer 的正面判讀只來自同一位使用者的觸感與單次測試，沒有逐 pin、接頭溫度或重複測試資料。',
        'url': 'https://www.techpowerup.com/forums/threads/close-call-5090-burnt-cable.334508/post-5772478'
    },
])

# 2026-08-19 weekly refresh: only threads whose visible post body and comments were read.
rows.extend([
    {
        'date': '2025-10-10', 'source': 'Hardwareluxx Forum', 'keyword': 'WireView', 'match': '內文＋留言',
        'title': 'WireView Pro 2 Logging 與 Ampinel 比較討論',
        'summary': 'Hardwareluxx 使用者因 Ampinel 議題重新比較兩款裝置，表示 WireView Pro 2 的外殼、內建小風扇與顯示器呈現較吸引他。',
        'comments': '討論也反映使用者認為不應需要額外的 Logging／監控裝置來補救 GPU 廠商問題；這是產品價值與產業責任的看法，不是 WireView 的保護實測。',
        'url': 'https://www.hardwareluxx.de/community/threads/wireview-pro-2-mit-logging-funktion-thermal-grizzly-mit-deltamate-wasserk%C3%BChler-und-der8enchtable.1367906/'
    },
    {
        'date': '2025-03-11', 'source': 'Hardwareluxx Forum', 'keyword': 'WireView', 'match': '留言',
        'title': 'WireView Pro 是否能作為 12V-2x6 安全方案',
        'summary': 'Hardwareluxx 使用者詢問 WireView Pro 是否能防止接頭熔損，以及問題是否只在遊戲高負載時發生。',
        'comments': '回覆指出 WireView 警報後可避免接頭繼續熔損，並可接第二個溫度感測器監控 PSU 端；另一則回覆明確表示沒有絕對安全方案，故障可能在 GPU 端、PSU 端、兩端線材或線材內部。',
        'url': 'https://www.hardwareluxx.de/community/threads/12vhpwr-12v-2x6-problematik-boardpartner-mit-bedenken-und-fehlgeschlagenen-l%C3%B6sungsans%C3%A4tzen.1364153/page-9'
    },
])

rows.extend([
    {
        'date': '2026-08-03', 'source': 'Reddit', 'keyword': 'WireView',
        'match': '標題＋內文＋留言',
        'title': 'Is the Thermal Grizzly WireView Pro II worth buying for the RTX 5070?',
        'summary': 'RTX 5070 買家因 12V-2x6 熔損新聞詢問是否值得加裝 WireView Pro II；顯示卡最高功耗約 250W，且 PSU 已有原生線材。主文反映低功耗卡使用者仍會因接頭風險考慮高價監控裝置。',
        'comments': '多數留言認為 250W 等級沒有必要花約 200 美元，應先確保使用 PSU 原生線並完全插妥；少數人則認為裝置可留待日後升級，或因喜歡監控而值得購買。已有 Astral 內建逐 pin 監控的使用者也表示不會重複購買。這是成本效益與使用者焦慮的討論，沒有保護觸發測試。',
        'url': 'https://www.reddit.com/r/ThermalGrizzly/comments/1vebo4v/is_the_thermal_grizzly_wireview_pro_ii_worth/'
    },
    {
        'date': '2026-07-31', 'source': 'Reddit', 'keyword': 'ROG Equalizer',
        'match': '內文＋留言',
        'title': 'CableMod cable compared with ROG Equalizer on RTX 5090 Astral',
        'summary': '發文者在兩套相同 RTX 5090 Astral／9950X3D 系統使用 CableMod 12V-2x6 線材，表示兩條線的逐 pin 分配都比自己先前的 ROG Equalizer 更平均；這是兩條線、兩套系統的個人觀察，沒有公開完整負載表。',
        'comments': '留言者主張線材均流有個體差異，不應由價格推論結果。發文者另回報曾因 Lian Li extension 造成異常而觸發 Astral／GPU Tweak 3 的逐 pin 保護，並強調選線與監控的重要性；但本串不能證明 CableMod 普遍優於 Equalizer。',
        'url': 'https://www.reddit.com/r/cablemod/comments/1vbiwey/i_am_very_happy_with_this_cablemod_12v2x6_cable/'
    },
    {
        'date': '2026-07-31', 'source': 'TechPowerUp Forums',
        'keywords': ['ThermalProtect', 'ROG Equalizer'],
        'match': '留言＋後續回覆',
        'title': 'RTX 4090 cable care discussion — ThermalProtect／Equalizer recommendation',
        'summary': '留言者建議 RTX 4090 擁有者妥善保養，並把 ThermalProtect 或 ROG Equalizer 列為可降低熔損風險的安全線材；若不更換，也建議考慮更新老化線材。這是個人建議，不是產品觸發或對照測試。',
        'comments': '被回覆者表示自己長期降壓，原廠線已改為 CableMod，第一條線故障後曾更換；自 2022 年 11 月以來未發生熔損。回覆沒有實際使用 ThermalProtect 或 Equalizer，因此只納入使用者對安全線材的認知與換線需求。',
        'url': 'https://www.techpowerup.com/forums/threads/nvidia-rtx-50-series-gpus-could-see-another-20-30-price-hike-in-2026.351234/post-5762766'
    },
    {
        'date': '2026-07-30', 'source': 'Reddit', 'keyword': 'ThermalProtect',
        'match': '標題＋內文＋留言',
        'title': 'New NVIDIA user considering Corsair ThermalProtect for RTX 5080',
        'summary': 'PNY RTX 5080 使用者雖以 Seasonic Focus GX 1000W ATX 3.x 原生線通過壓力測試，仍因網路熔損案例詢問是否應換 Corsair ThermalProtect，以及換線是否反而增加風險。',
        'comments': '多數留言認為 5080 功耗低於 5090，完全插妥、避免側板擠壓與使用原生線更重要；也有人建議 ThermalProtect 或額外溫度探頭。留言對 5080 是否存在風險意見不一，且沒有 ThermalProtect 擁有者觸發案例；可確認的需求是相容性、品質與「換線是否更安全」的明確指引。',
        'url': 'https://www.reddit.com/r/RTX5080/comments/1vaveb8/new_nvidia_user_scared_of_the_12v2x6_cable/'
    },
    {
        'date': '2026-07-29', 'source': 'Reddit', 'keyword': 'Ampinel',
        'match': '標題＋內文＋留言',
        'title': 'Bad experience with Aqua Computer Ampinel (two faulty units)',
        'summary': 'RTX 5090 Ventus 使用者回報第一顆 Ampinel 到貨時第 2 pin 已後縮並亮黃燈，換貨後第二顆使用兩天正常，第三天 Aquasuite 顯示第 1 pin 為 0A；低負載時沒有告警，執行內建 render test 後才告警。關機拆檢發現第 1 pin 燒痕及另一 pin 後縮、歪斜，GPU 原生接頭未受損。發文者表示兩次都完全插妥、線材對齊，且裝置未碰背板，最後決定退款。',
        'comments': 'Aqua Computer 回覆無法遠端判定根因，將檢驗退回裝置；並說明預設只有總電流達 20A 以上時，單路 0A 才會觸發缺相告警，低負載未告警屬預期行為。其他擁有者經驗分歧：有人使用一個多月無問題；一人 Rev.4 曾有問題、Rev.5 暫時正常；另一人 Rev.4 pin 難插，換 Rev.5 後正常。這些案例不能換算失效率，但明確指出端子後縮、版本差異、低負載告警邏輯與出廠品管需要調查。',
        'url': 'https://www.reddit.com/r/watercooling/comments/1v9co9h/bad_experience_with_aqua_computer_ampinel_two/'
    },
    {
        'date': '2026-07-29', 'source': 'Reddit', 'keyword': 'WireView',
        'match': '標題＋內文＋留言',
        'title': 'WireView Pro II Wired: balanced readings on an older ATX 2.x PSU',
        'summary': 'RTX 4090 Strix 使用者以約六年舊 EVGA SuperNOVA 1200W、四條 8-pin 轉 12VHPWR 線及 666W BIOS 跑 FurMark，HWiNFO 截圖顯示六路最大電流差約 0.3A、功率差約 4W；發文者因此對舊 PSU 與重度超頻的接線狀態較放心。',
        'comments': '另一名 5090 FE／ATX 2.x PSU 使用者也稱逐 pin 平衡；另有 5070 Ti 使用者回報峰值差約 0.7A。留言同時提醒這些只是各自系統的讀值，不能證明特定 PSU 品牌必然較穩，也沒有故障注入或長期接點檢驗。',
        'url': 'https://www.reddit.com/r/ThermalGrizzly/comments/1v9oiu4/wireview_pro_2_wired_shockingly_beautiful_results/'
    },
    {
        'date': '2026-07-01', 'source': 'Reddit',
        'keywords': ['GPU Shield', 'ThermalProtect'],
        'match': '標題＋內文＋留言',
        'title': 'Cooler Master GPU Shield availability',
        'summary': '發文者曾遇到 12V-2x6 接頭接近熔損，正在找可主動處置異常的方案；他認為 ThermalProtect 的溫度觸發位置未必涵蓋所有故障點，因此詢問 GPU Shield 是否會推出可搭配既有 PSU 的獨立轉接器。',
        'comments': '可見留言沒有提供上市日期或實測，只反映「不想為保護功能更換整顆 PSU」的需求；本串不能證明 GPU Shield 的保護效果。',
        'url': 'https://www.reddit.com/r/coolermaster/comments/1ukfz35/gpu_shield_availability/'
    },
    {
        'date': '2026-07-01', 'source': 'Reddit',
        'keywords': ['WireView', 'GPU Safeguard'],
        'match': '內文＋留言',
        'title': 'WireView Pro II or MSI MPG Ai1300TS for 5090 protection',
        'summary': '發文者比較 GPU 端 WireView Pro II 與整合 Safeguard+ 的 Ai1300TS；兩者都能提供逐 pin 監控與異常處置，但前者可保留既有 PSU，後者把感測與控制整合在 PSU。',
        'comments': '留言主要比較總成本、重複監控與安裝空間；沒有形成單一最佳答案，也沒有直接測試兩者在相同故障下的反應。',
        'url': 'https://www.reddit.com/r/buildapc/comments/1uk175h/wireview_pro_ii_or_msi_mpg_ai1300ts/'
    },
    {
        'date': '2026-06-19', 'source': 'Reddit', 'keyword': 'GPU Safeguard',
        'match': '標題＋內文＋留言',
        'title': 'MSI Safeguard+ shutdown behavior test',
        'summary': '使用者把單 pin 門檻設為 7A 後測試 Safeguard+，觸發時整台電腦直接關機；正常使用時，他觀察到高低 pin 約 9A／1A 的差異。',
        'comments': '留言建議先降低 GPU power profile，再逐步驗證門檻。另有使用者提到韌體仍有較高的硬體保護門檻，但本串沒有獨立量測其精確值；可確認的是自訂門檻確實觸發過關機。',
        'url': 'https://www.reddit.com/r/MSI_Gaming/comments/1u9nci0/safeguard_shutdown_behavior/'
    },
    {
        'date': '2026-06-13', 'source': 'Reddit', 'keyword': 'GPU Safeguard',
        'match': '內文＋留言',
        'title': 'Tune MSI Safeguard+ thresholds through PSU.cfg',
        'summary': '發文者整理 PSU.cfg 中 MaxCurrent、CurrentDif 與 SoftwareAlarm 等欄位的調整步驟，用來改變單 pin 電流與 pin 間差異的軟體告警／降載條件。',
        'comments': '留言把它視為進階設定方法，但也提醒設定錯誤可能造成頻繁告警或關機；本串是使用者實作，不是 MSI 公布的完整安全門檻規格。',
        'url': 'https://www.reddit.com/r/MSI_Gaming/comments/1u4c5i6/tune_msi_safeguard_via_psucfg/'
    },
    {
        'date': '2026-06-07', 'source': 'Reddit', 'keyword': 'OptiGuard',
        'match': '標題＋內文＋留言',
        'title': 'OptiGuard consumer release delay',
        'summary': '發文者因 OptiGuard 消費版遲遲未上市而詢問時程；討論提到其跨 PSU 平台與藍牙監控構想，但沒有可購買產品可供驗證。',
        'comments': '數名留言者已改買 MSI Ai1600TS；一名使用者回報自己的 Ai1600TS 有異音。另有人引述客服回覆指向 2026 年稍後，但本串沒有正式上市日期。',
        'url': 'https://www.reddit.com/r/Seasonic/comments/1tz26pm/optiguard_release_delay/'
    },
    {
        'date': '2026-06-05', 'source': 'Reddit', 'keyword': 'Ampinel',
        'match': '標題＋內文＋留言',
        'title': 'Ampinel owner experience after preorder',
        'summary': '一名使用者在約四個月預購等待後安裝 Ampinel；他表示裝置需要約 50 mm 空間，並觀察到 PSU 端溫度由約 50–58°C 降至 40–45°C、約 400W 負載時各 pin 約 5–6A。',
        'comments': '發文者肯定監控與控制功能，並認為它改善了自己的連接問題；這是單一使用者、單一系統的回報，沒有對照測試，不能推論普遍降溫幅度。',
        'url': 'https://www.reddit.com/r/watercooling/comments/1twuei3/ampinel/'
    },
    {
        'date': '2026-05-25', 'source': 'Reddit', 'keyword': 'GPU Safeguard',
        'match': '留言',
        'title': 'MSI MPG Ai1600TS per-pin monitoring discussion',
        'summary': '原始主文已刪除；可見留言仍直接討論 Ai1600TS 的逐 pin 監控、較低瓦數版本需求與 Afterburner 顯示。',
        'comments': '一名實際使用者表示各 pin 電流接近且 Afterburner 可讀取資料；其他人希望推出較低功率、較低價格型號。因主文已刪除，本筆只採用可見留言。',
        'url': 'https://www.reddit.com/r/MSI_Gaming/comments/1tndr1f/msi_mpg_ai1600ts_perpin_current_monitoring/'
    },
    {
        'date': '2026-05-23', 'source': 'Reddit', 'keyword': 'Titanload',
        'match': '標題＋內文＋留言',
        'title': 'Segotep Titanload cable owner impression',
        'summary': '使用者收到 Titanload 後肯定做工與端子質感，並表示將進一步進行高負載測試。',
        'comments': '留言認為強化線材可增加餘裕，但反覆指出它沒有改變 GPU 端接頭本身的結構風險；本串當下尚未提供長時間或故障注入測試。',
        'url': 'https://www.reddit.com/r/nvidia/comments/1tld0vb/segotep_titanload_cable/'
    },
    {
        'date': '2026-05-19', 'source': 'Reddit',
        'keywords': ['GPU Safeguard', 'WireView'],
        'match': '內文＋留言',
        'title': 'Melted connector on MSI MEG Ai1600T',
        'summary': '使用者回報 MEG Ai1600T 的 GPU 與 PSU 端接頭熔損，顯示卡仍可運作並進入 RMA；他因此考慮改用具逐 pin 監控的 Ai1600TS 或增加 WireView。',
        'comments': '留言要求檢查插入狀態、線材與兩端接點，也質疑僅在 PSU 端監控是否足夠。本串是單一故障案例，沒有確定根因。',
        'url': 'https://www.reddit.com/r/MSI_Gaming/comments/1tgsqs4/burned_meg_ai1600t_connector/'
    },
    {
        'date': '2026-05-18', 'source': 'Reddit',
        'keywords': ['WireView', 'GPU Safeguard'],
        'match': '標題＋內文＋留言',
        'title': 'WireView Pro II Wired preorder and installation concerns',
        'summary': '使用者以約 175 美元預購 Wired 版，預估等待五至六週；討論重點包含它能連接主機電源按鈕自動關機，以及有線版本的溫度感測位置。',
        'comments': '有留言擔心有線版沒有直接量測 GPU 接頭溫度；另有使用者拆原線時損傷 GPU 卡扣，顯示拆裝風險。也有人把整合式 Safeguard+ 列為替代方案。',
        'url': 'https://www.reddit.com/r/ThermalGrizzly/comments/1tg7kfy/wireview_pro_ii_wired_preorder/'
    },
    {
        'date': '2026-05-12', 'source': 'Reddit', 'keyword': 'ThermalProtect',
        'match': '標題＋內文＋留言',
        'title': 'ThermalProtect test-method clarification',
        'summary': '討論指出某測試只量到電流，卻沒有控制 ThermalProtect 感測點的實際溫度；因此不同觸發時間不能直接解讀為產品反應不一致。',
        'comments': 'CORSAIR 帳號在留言說明產品依溫度而非電流值觸發，環境溫度與加熱方式會影響時間；此串強化了公開標示感測位置、門檻與測試條件的需求。',
        'url': 'https://www.reddit.com/r/Corsair/comments/1takym6/testing_thermalprotect_problem/'
    },
    {
        'date': '2026-05-04', 'source': 'Reddit',
        'keywords': ['ROG Equalizer', 'ThermalProtect'],
        'match': '標題＋內文＋留言',
        'title': 'ROG Equalizer does not make sense to me',
        'summary': '發文者質疑被動 busbar 線材是否能處理接觸不良；討論把它與有溫度觸發處置的 ThermalProtect 比較。',
        'comments': '支持者認為 Equalizer 能增加熱與電流餘裕，反對者認為它只是延後問題且增加材料浪費；本串沒有同平台實測，呈現的是對設計機制的分歧。',
        'url': 'https://www.reddit.com/r/ASUSROG/comments/1t331yd/rog_equalizer_doesnt_make_sense/'
    },
    {
        'date': '2026-05-02', 'source': 'Reddit', 'keyword': 'ThermalProtect',
        'match': '標題＋內文＋留言',
        'title': 'CORSAIR ThermalProtect technical introduction',
        'summary': '官方帳號說明感測梳位於 GPU 接頭約 30 mm 處，約 65°C 時改變 sense pin 狀態，讓 GPU 在毫秒級停止或降低取電；適用原生 12V-2x6 PSU。',
        'comments': '使用者主要追問 Type 4／Type 5 舊款 PSU 相容版本及實際故障測試。官方表示其他版本稍後推出；當時留言未提供長期使用案例。',
        'url': 'https://www.reddit.com/r/Corsair/comments/1t19mcd/corsair_thermalprotect_technical_overview/'
    },
    {
        'date': '2026-04-28', 'source': 'Reddit', 'keyword': 'ThermalProtect',
        'match': '標題＋留言',
        'title': 'ThermalProtect review discussion',
        'summary': '主文分享外部評測；可見留言認為被動溫度開關是簡潔的保護層，但觸發效果取決於熱源位置與升溫速度。',
        'comments': '留言要求 Type 4／Type 5 相容版本，並與 Equalizer 的被動強化方式比較；沒有留言宣稱它能涵蓋所有熔損模式。',
        'url': 'https://www.reddit.com/r/hardware/comments/1sy32o6/corsair_thermalprotect_review/'
    },
    {
        'date': '2026-04-28', 'source': 'Reddit', 'keyword': 'ThermalProtect',
        'match': '標題＋內文＋留言',
        'title': 'CORSAIR ThermalProtect launch',
        'summary': '上市資訊確認首版只支援具有原生 12V-2x6 PSU 端口的電源供應器，透過線材內溫度開關觸發 GPU 降載或斷電。',
        'comments': '多名使用者詢問 HX1500i 與 Type 4／5 支援，反映相容性辨識不清；CORSAIR 回覆其他線材版本將後續推出。',
        'url': 'https://www.reddit.com/r/Corsair/comments/1sy1ojm/corsair_launches_thermalprotect/'
    },
    {
        'date': '2026-04-25', 'source': 'Reddit', 'keyword': 'ROG Equalizer',
        'match': '標題＋內文＋留言',
        'title': 'ROG Equalizer listed for US$49.99',
        'summary': '使用者發現 ROG Equalizer 在 ASUS 商店以 49.99 美元上架，並討論是否可跨不同 PSU 品牌使用。',
        'comments': '部分人認為價格相對高，另一些人把它視為高價 GPU 的低成本保險；留言也要求清楚的 PSU 相容清單與升級方案。',
        'url': 'https://www.reddit.com/r/ASUSROG/comments/1sv8z2j/rog_equalizer_store_4999/'
    },
    {
        'date': '2026-04-20', 'source': 'TechPowerUp Forums', 'keyword': 'OptiGuard',
        'match': '留言',
        'title': 'ROG Equalizer discussion — waiting for Seasonic OptiGuard tests',
        'summary': '留言者表示較看好 Seasonic OptiGuard，但要等待產品與測試結果後才會判斷。',
        'comments': '這是購買意向，不是 OptiGuard 使用經驗；可確認的痛點是消費版尚缺上市與第三方測試。',
        'url': 'https://www.techpowerup.com/forums/threads/asus-introduces-rog-equalizer-12v-2x6-cable-for-gpu-power-stability.348123/post-5710438'
    },
    {
        'date': '2026-04-16', 'source': 'TechPowerUp Forums', 'keyword': 'T-Guard',
        'match': '主文＋留言',
        'title': "GIGABYTE's new gaming PSUs with exclusive T-Guard",
        'summary': '產品發布文說明 T-Guard 以熱敏元件即時監控 12V-2x6 接頭，異常時警示並隔離或降低 GPU 供電，系統可保持運作以便儲存工作。',
        'comments': '可見留言主要討論接頭標準與保護必要性，沒有實際擁有者觸發測試；本筆只證實產品宣稱的機制。',
        'url': 'https://www.techpowerup.com/forums/threads/gigabytes-new-gaming-psus-secure-top-tier-gpus-with-exclusive-t-guard.348271/'
    },
    {
        'date': '2026-04-11', 'source': 'Reddit',
        'keywords': ['ROG Equalizer', 'GPU Safeguard', 'OptiGuard', 'WireView'],
        'match': '內文＋留言',
        'title': '12V-2x6 protection products compared',
        'summary': '討論把 MSI Safeguard、ROG Equalizer、Seasonic OptiGuard 與 WireView 並列，比較主動監控／處置、被動強化與外接監控的差異。',
        'comments': '留言對各產品的門檻與效果有不少推測，且反覆指出多數方案當時缺少統一測試；因此本筆只採用可確認的功能比較與「市場資訊混亂」這項共識。',
        'url': 'https://www.reddit.com/r/hardware/comments/1si0vi4/12v2x6_protection_options_equalizer_safeguard/'
    },
    {
        'date': '2026-04-10', 'source': 'Reddit',
        'keywords': ['ROG Equalizer', 'Titanload'],
        'match': '標題＋內文＋留言',
        'title': 'ROG Equalizer cable mechanism discussion',
        'summary': '發文者整理 Equalizer 的高載流接點與 busbar 設計，但質疑其沒有主動電子均流電路，並指出當時價格與完整規格不清楚。',
        'comments': '留言提到 Titanload 採高載流端子但美國不易取得；多數討論要求以相同平台量測各 pin、溫度與長時間負載，而非只比較額定值。',
        'url': 'https://www.reddit.com/r/ASUSROG/comments/1sgxfk3/rog_equalizer_12v2x6_cable/'
    },
    {
        'date': '2026-04-09', 'source': 'Reddit', 'keyword': 'GPU Safeguard',
        'match': '內文＋留言',
        'title': 'MSI Ai1600TS technical review discussion',
        'summary': '主文分享 Ai1600TS 技術評測；留言焦點是逐 pin 監控與 Safeguard+ 是否值得升級，以及各地實際供貨。',
        'comments': '一名 Ai1600T 使用者表示購買後才發現舊型號沒有逐 pin 監控；其他人詢問美國、澳洲與歐洲的 Ai1300TS／Ai1600TS 供貨，顯示型號命名與功能差異需要更清楚。',
        'url': 'https://www.reddit.com/r/MSI_Gaming/comments/1sgb4pz/msi_ai1600ts_technical_review/'
    },
    {
        'date': '2026-04-07', 'source': 'TechPowerUp Forums', 'keyword': 'GPU Safeguard',
        'match': '留言',
        'title': 'Double 12VHPWR connectors discussion — MSI GPU Safeguard',
        'summary': '留言指出當時尚未看到售價，並說明 MSI GPU Safeguard 以逐 pin 電流監控偵測異常。',
        'comments': '可見內容是功能與價格等待，沒有實際觸發或長期測試。',
        'url': 'https://www.techpowerup.com/forums/threads/double-12vhpwr-connectors-in-the-future-graphics-cards-may-resolve-overheating-and-melting-cables.346653/post-5704363'
    },
    {
        'date': '2026-03-25', 'source': 'TechPowerUp Forums', 'keyword': 'GPU Safeguard',
        'match': '留言',
        'title': 'MSI Safeguard software dependency question',
        'summary': '留言者詢問 Safeguard+ 是否必須啟用廠商常駐軟體，或可直接透過 Afterburner 使用。',
        'comments': '此筆沒有實測結論，但明確反映使用者不希望核心保護依賴額外軟體。',
        'url': 'https://www.techpowerup.com/forums/threads/msi-announces-safeguard-for-its-mpg-ai-ts-series-psus.347699/post-5697608'
    },
    {
        'date': '2026-03-25', 'source': 'TechPowerUp Forums', 'keyword': 'GPU Safeguard',
        'match': '主文＋留言',
        'title': 'MSI announces Safeguard for MPG AI TS PSUs',
        'summary': '發布文說明逐 pin 即時監控、不平衡／過載偵測、蜂鳴器與彈窗警示，以及透過 Afterburner 套用 GPU 降載。',
        'comments': '留言肯定逐 pin 可視性，但質疑軟體依賴、售價及為何接頭本身問題仍需額外保護；沒有使用者長期測試。',
        'url': 'https://www.techpowerup.com/forums/threads/msi-announces-safeguard-for-its-mpg-ai-ts-series-psus.347699/'
    },
    {
        'date': '2026-03-24', 'source': 'Reddit', 'keyword': 'WireView',
        'match': '標題＋內文＋留言',
        'title': 'WireView Pro II red LED and no signal',
        'summary': 'Astral RTX 5090 使用者安裝 WireView Pro II 後遇到紅燈、無畫面與零讀值，拆除裝置後恢復正常。',
        'comments': 'Thermal Grizzly 很快寄出替換品且不要求先退回，售後獲肯定；本串沒有公布故障分析，因此只能確認該單一裝置相容／故障案例。',
        'url': 'https://www.reddit.com/r/ThermalGrizzly/comments/1s1yd6w/wireview_pro_ii_red_led_no_signal/'
    },
    {
        'date': '2026-03-20', 'source': 'Reddit', 'keyword': 'WireView',
        'match': '標題＋內文＋留言',
        'title': 'WireView Pro II thoughts after one month',
        'summary': '使用者一個月後認為做工與安裝體驗良好；他透過整理線材彎折、換線與更新韌體改善逐 pin 不平衡，但仍偶爾看到 VR 警告。',
        'comments': '發文者肯定客服回應與 HWiNFO 整合，同時認為價格高、cutoff 線安裝較麻煩；此筆提供中期使用經驗，但不是故障注入測試。',
        'url': 'https://www.reddit.com/r/ThermalGrizzly/comments/1ry7pkp/wireview_pro_ii_thoughts/'
    },
    {
        'date': '2026-02-28', 'source': 'Reddit',
        'keywords': ['WireView', 'OptiGuard'],
        'match': '內文＋留言',
        'title': 'WireView or a new PSU for 5090 protection',
        'summary': '使用者在舊 PSU 加 WireView與直接換原生 12V-2x6 PSU 間選擇；留言多建議先使用原生線材，再視需要加監控。',
        'comments': '數名留言者表示會在 OptiGuard 上市前以 WireView 過渡，也抱怨 Seasonic 沒有明確時程；沒有直接比較兩者保護效果。',
        'url': 'https://www.reddit.com/r/buildapc/comments/1rgn8y3/wireview_or_new_psu/'
    },
    {
        'date': '2026-02-11', 'source': 'Reddit', 'keyword': 'GPU Safeguard',
        'match': '內文＋留言',
        'title': 'Waiting for lower-wattage MSI TS PSUs',
        'summary': '使用者詢問 Ai1300TS／Ai1600TS 的上市狀況，關注點是 Safeguard+ 逐 pin 監控而非總瓦數。',
        'comments': '留言釐清產品主要量測各 pin 電流而非直接量測每個端子的溫度，也有人要求較低瓦數與價格版本。',
        'url': 'https://www.reddit.com/r/MSI_Gaming/comments/1r19f4o/no_new_msi_ts_psu/'
    },
    {
        'date': '2026-02-10', 'source': 'Reddit',
        'keywords': ['Ampinel', 'WireView'],
        'match': '標題＋內文＋留言',
        'title': 'Ampinel versus WireView',
        'summary': '討論區分 Ampinel 的主動電流平衡與 WireView 的監控／告警，並比較是否需要延長線與 GPU 端安裝空間。',
        'comments': '使用者擔心 Ampinel 對凹入式接頭、Founders Edition 與 180 度安裝的相容性；本串沒有同平台效能或保護測試。',
        'url': 'https://www.reddit.com/r/watercooling/comments/1r0sbzj/ampinel_vs_wireview/'
    },
    {
        'date': '2026-02-10', 'source': 'Reddit', 'keyword': 'Ampinel',
        'match': '標題＋內文＋留言',
        'title': 'Aqua Computer Ampinel launch discussion',
        'summary': '發布討論介紹主動均流、監控與 AquaSuite 整合，並說明核心保護在沒有軟體時仍可運作。',
        'comments': '使用者肯定 AquaSuite 生態，但對約 100 歐元價格及軟體更新訂閱有疑慮；當時留言尚無長期擁有者測試。',
        'url': 'https://www.reddit.com/r/watercooling/comments/1r0f73x/aqua_computer_ampinel_launch/'
    },
    {
        'date': '2026-02-01', 'source': 'Reddit', 'keyword': 'WireView',
        'match': '標題＋內文＋留言',
        'title': 'WireView Pro II found a bad cable before damage',
        'summary': 'RTX 4090 使用者看到第 3 pin 僅約 0.8A；重新插拔沒有改善，更換 MODDIY 線材後各 pin 恢復接近，因而在熔損前定位到線材問題。',
        'comments': '留言把它視為逐 pin 監控的實際價值，但也提醒這只是單一案例，且異常來源是線材還是端子仍需檢查。',
        'url': 'https://www.reddit.com/r/ThermalGrizzly/comments/1qsczjr/wireview_saved_my_4090/'
    },
    {
        'date': '2026-01-27', 'source': 'Reddit', 'keyword': 'WireView',
        'match': '標題＋內文＋留言',
        'title': 'Do I need WireView Pro II with an Astral GPU?',
        'summary': 'Astral 使用者詢問顯示卡既有 HWiNFO 逐 pin 告警後，WireView 是否仍有必要。',
        'comments': '部分留言認為功能重複，只剩風扇、外觀與 Wired 關機價值；其他人仍願意為額外可視性與安心付費。此串顯示內建監控 GPU 的價值主張需要分眾。',
        'url': 'https://www.reddit.com/r/ThermalGrizzly/comments/1qo6uz9/do_i_need_wireview_pro_ii/'
    },
    {
        'date': '2026-01-24', 'source': 'Reddit', 'keyword': 'WireView',
        'match': '內文＋留言',
        'title': 'Persistent pin 2 / pin 6 current imbalance',
        'summary': 'Ventus OC 使用者用三條線、兩顆 PSU 仍看到相近的第 2／6 pin 不平衡，並整理其他 MSI 卡的類似回報。',
        'comments': '留言無法確定是 GPU 內部分配、接點或量測差異；反映監控工具需要趨勢、基準與故障定位指引，避免只給單次數字。',
        'url': 'https://www.reddit.com/r/ThermalGrizzly/comments/1qlnurz/pin2_pin6_current_imbalance_summary/'
    },
    {
        'date': '2026-01-22', 'source': 'Reddit',
        'keywords': ['GPU Safeguard', 'WireView'],
        'match': '內文＋留言',
        'title': 'MSI Safeguard for RTX 5090',
        'summary': '已使用 WireView 的發文者詢問 Safeguard+；留言說明軟體可設定異常後的自動處置。',
        'comments': '一名使用者回報某 pin 變成 0A 後收到警示並換線，認為功能避免進一步風險；這是單一案例，沒有公開事件紀錄或硬體檢驗。',
        'url': 'https://www.reddit.com/r/MSI_Gaming/comments/1qjuogh/msi_safeguard_for_5090/'
    },
    {
        'date': '2026-01-15', 'source': 'Reddit',
        'keywords': ['WireView', 'GPU Shield', 'GPU Safeguard', 'Ampinel'],
        'match': '內文＋留言',
        'title': 'A new market for 12V-2x6 protection products',
        'summary': '發文者把 WireView、GPU Shield、Safeguard+ 與 Ampinel 視為因 12V-2x6 風險形成的新產品類別。',
        'comments': '留言一方面詢問是否真的需要額外裝置，另一方面批評接頭問題不應轉嫁給消費者購買配件；本串沒有產品實測。',
        'url': 'https://www.reddit.com/r/hardware/comments/1qd2ljm/new_12v2x6_protection_business_segment/'
    },
    {
        'date': '2026-01-13', 'source': 'Reddit',
        'keywords': ['WireView', 'GPU Shield'],
        'match': '內文＋留言',
        'title': 'Looking for 12V-2x6 safety options',
        'summary': '使用者因擔心火災而比較 WireView 與 GPU Shield，但找不到 GPU Shield 的獨立產品頁與上市資訊。',
        'comments': '留言多建議正確插入、避免彎折與監控；沒有 GPU Shield 實際使用者，因此只反映資訊與可購買性缺口。',
        'url': 'https://www.reddit.com/r/buildapc/comments/1qbdeit/12v2x6_safety_options/'
    },
    {
        'date': '2026-01-08', 'source': 'Reddit', 'keyword': 'GPU Safeguard',
        'match': '標題＋留言',
        'title': 'MSI GPU Safeguard discussion',
        'summary': '主文分享 Safeguard 產品資訊；留言焦點不是實測，而是批評產業以額外保護補救接頭設計。',
        'comments': '可見留言沒有提供觸發數據或使用經驗，因此本筆只作為早期市場反應。',
        'url': 'https://www.reddit.com/r/hardware/comments/1q757kn/msi_gpu_safeguard/'
    },
    {
        'date': '2026-01-07', 'source': 'Reddit', 'keyword': 'GPU Shield',
        'match': '標題＋留言',
        'title': 'Cooler Master GPU Shield at CES',
        'summary': '產品貼文介紹 GPU Shield 與 MWE Gold V4 PSU；可見留言只詢問上市與可購買時間。',
        'comments': '沒有使用者實測，不能判斷保護效果；可確認的是早期需求集中於供貨資訊。',
        'url': 'https://www.reddit.com/r/coolermaster/comments/1q6adeu/cooler_master_gpu_shield_ces/'
    },
    {
        'date': '2026-01-06', 'source': 'Reddit', 'keyword': 'GPU Safeguard',
        'match': '標題＋內文＋留言',
        'title': 'MSI Safeguard+ introduction',
        'summary': '討論介紹蜂鳴警示、Afterburner 彈窗、降載與延遲關機；使用者特別關心異常後是否應立即切斷供電。',
        'comments': '意見分歧：有人要求立即硬切以保護硬體，也有人希望保留數秒儲存工作。這形成可設定但受安全上限約束的處置需求。',
        'url': 'https://www.reddit.com/r/MSI_Gaming/comments/1q54sc7/msi_safeguard_plus_intro/'
    },
    {
        'date': '2026-01-04', 'source': 'Reddit',
        'keywords': ['OptiGuard', 'WireView'],
        'match': '標題＋內文＋留言',
        'title': 'Waiting for Seasonic OptiGuard',
        'summary': '使用者詢問 OptiGuard 上市時間，並在等待 OptiGuard與先買 WireView 間選擇。',
        'comments': '留言討論第一代硬切與後續作業系統通知的取捨，也要求 USB／系統感知的安全關機；沒有可購買樣品或實測。',
        'url': 'https://www.reddit.com/r/Seasonic/comments/1q3fjo6/seasonic_optiguard_release_date/'
    },
    {
        'date': '2026-01-03', 'source': 'Reddit', 'keyword': 'WireView',
        'match': '標題＋內文＋留言',
        'title': 'WireView Pro II connection wear question',
        'summary': '使用者詢問即使不移動線材，接點是否仍會隨時間劣化，並關注 GPU 端新增溫度感測是否能及早發現問題。',
        'comments': '留言要求把 GPU 端、轉接器端與線材端的數據分開，協助判斷真正故障點；沒有長期壽命數據。',
        'url': 'https://www.reddit.com/r/ThermalGrizzly/comments/1q26js8/wireview_pro2_connection_wear/'
    },
    {
        'date': '2026-01-03', 'source': 'Reddit', 'keyword': 'WireView',
        'match': '標題＋內文＋留言',
        'title': 'WireView extension for Founders Edition',
        'summary': '發文者因 Founders Edition 空間與方向問題希望使用延長方案。',
        'comments': '留言擔心額外接點增加診斷與保固不確定性，也指出安裝方向、固定方式與機殼空間是採用障礙。',
        'url': 'https://www.reddit.com/r/ThermalGrizzly/comments/1q2dbfa/wireview_extension_for_fe/'
    },
])

# 2026-08-05 weekly refresh.  These rows were admitted only after the visible
# Reddit post body and comments had been read; near-duplicate crossposts are
# represented by the discussion with the fuller comment context.
rows.extend([
    {
        'date': '2026-08-03', 'source': 'Reddit', 'keyword': 'ROG Equalizer',
        'match': '標題＋內文',
        'title': 'ROG EQUALIZER VS SERIE THOR 3',
        'summary': '發文者以 RTX 5090 Astral OC 在預設、未超頻狀態做一次壓力測試：ROG Equalizer 在最高約 600W 時沒有任何 pin 超過 9A；同一張卡改用 Thor III 電源供應器隨附線材時，單 pin 超過 9.2A，ASUS 軟體與 HWiNFO 都發出警報。這是單一系統的快速比較，主文未交代重複次數或其他控制條件。',
        'comments': '本次讀取頁面時未見使用者留言，只有相關貼文連結；因此不能由此判斷長期穩定性、不同線材是否完全同條件，或推論所有系統都會得到相同結果。',
        'url': 'https://www.reddit.com/r/ASUSROG/comments/1velpgc/rog_equalizer_vs_serie_thor_3/'
    },
    {
        'date': '2026-08-01', 'source': 'Reddit', 'keyword': 'ROG Equalizer',
        'match': '標題＋內文＋留言',
        'title': 'ROG Equalizer：RTX 5080 各 pin 相差約 2A 是否正常？',
        'summary': '發文者在 RTX 5080 上觀察到各 pin 差距：原本 DeepCool 1000W 約 0.4A，換成 ROG Strix 1200W Platinum 與 Equalizer 後，同一使用情境約 2A；系統仍可正常運作。發文者在留言補充遊戲功耗約 373W，並詢問是否代表接觸不良或需要換線。',
        'comments': '留言建議重新插拔或換線交叉測試；另一名使用者回報自己待機約差 0.6A、遊戲約差 2.2A。留言對「低於 10A 是否安全」及六條 power／ground pin 的解讀並不一致，且沒有後續測試或確定根因，因此本案只能確認使用者對讀值差異與門檻判讀感到不確定。',
        'url': 'https://www.reddit.com/r/RTX5080/comments/1vckxvp/rog_equalizer/'
    },
    {
        'date': '2026-07-28', 'source': 'Reddit', 'keyword': 'ROG Equalizer',
        'match': '標題＋內文＋留言',
        'title': 'Testing ROG Equalizer (Recommendation: ignore critics)',
        'summary': '發文者列出舊線材在「100%」時六路約 8.1、9.1、10.3、10.3、9.0、8.9A；換 Equalizer 後約 7A，據此認為可恢復 100% power limit。留言依數值反算後指出兩組總功率約 668W 與 529W，不是等功率比較，因此主文不能證明 Equalizer 在相同負載下改善均流。',
        'comments': '留言另指出，Equalizer 的橋接位置可能讓 Astral 只看到橋接後讀值，而智慧 PSU 看到橋接前讀值，兩端監測不等同完整路徑。擁有者經驗也不一致：有人因不平衡變差而退貨，有人表示值得購買，另有 RTX 5080 使用者稱使用一個月未見異常；都沒有提供一致的長期對照數據。',
        'url': 'https://www.reddit.com/r/ASUSROG/comments/1v8q6dy/testing_rog_equalizer_recommendation_ignore/'
    },
    {
        'date': '2026-07-27', 'source': 'Reddit',
        'keywords': ['ThermalProtect', 'ROG Equalizer', 'GPU Safeguard', 'WireView'],
        'match': '標題＋內文＋留言',
        'title': 'Corsair Thermal Protect Cable vs ROG GPU Power Detector / Equalizer',
        'summary': '發文者徵求 ThermalProtect 的長期使用、預警／保護效果、誤報，以及與 ROG Equalizer 的可靠性、易用性與安心感比較。可見內容沒有同時長期使用兩者的直接比較，也沒有新增 ThermalProtect 實際觸發案例。',
        'comments': 'Corsair 代表連結一項先前未按產品動作方式測試、後來依說明重測的外部影片；本報告未把影片結論當成論壇實測。另有一名 GPU Safeguard+ 擁有者表示使用感受良好並喜歡 Afterburner 整合。關於 Equalizer 燒毀圖片與 WireView 是否是唯一有效方案的說法互相衝突，留言沒有提供可核對原始證據，故不列為已證實事件。',
        'url': 'https://www.reddit.com/r/Corsair/comments/1v1xadu/corsair_thermal_protect_cable_vs_rog_gpu_power/'
    },
    {
        'date': '2026-07-25', 'source': 'Reddit', 'keyword': 'Ampinel',
        'match': '標題＋內文＋留言',
        'title': 'Ampinel Installed',
        'summary': 'MSI RTX 5090 Ventus／LYNK+ 水冷使用者肯定 Ampinel 軟體容易使用，但剛性外殼與水冷背板干涉，必須用 Dremel 切削鋁製背板才能完全插妥。留言亦更正：Ampinel 平衡的是電壓降，不應簡化寫成「負載平衡」。',
        'comments': '發文者第一顆 Ampinel 有輕微晃動且一個 pin 後縮，造成系統不穩，換貨後晃動與問題消失，重載時維持綠燈；另一名 eBay 買家也回報有晃動，偶爾一至兩 pin 顯示黃色。另有使用者因機殼／水冷配置需降低顯示卡位置。這些是少數擁有者案例，不能換算故障率，但直接指出端子品管、插接強度與空間相容性問題。',
        'url': 'https://www.reddit.com/r/watercooling/comments/1v5wh2i/ampinel_installed/'
    },
    {
        'date': '2026-06-10', 'source': 'Reddit', 'keyword': 'WireView',
        'match': '標題＋內文＋留言',
        'title': 'New WireView Pro II White defective on arrival?',
        'summary': '同時購買 Normal 與 Reverse 兩顆 WireView Pro II 的 RTX 5090 使用者回報：Reverse 在兩套系統都正常，Normal 則只顯示 0W、顯示卡無畫面、GPU 電源錯誤燈與主機板 VGA 錯誤同時出現。換測多條 Seasonic、be quiet!、CableMod 與 ASUS 線材仍相同。',
        'comments': 'Thermal Grizzly 人員依跨兩套系統、跨多條線材的結果判斷裝置看起來有缺陷，請使用者聯絡客服；發文者已寄信。沒有後續故障分析，因此只能確認單一 DOA／故障案例與客服處置。',
        'url': 'https://www.reddit.com/r/ThermalGrizzly/comments/1u20yj8/new_wireview_pro_ii_white_normal_defective/'
    },
    {
        'date': '2026-05-04', 'source': 'Reddit', 'keyword': 'WireView',
        'match': '標題＋內文＋留言',
        'title': 'WireView Pro II connection overheating and worsening imbalance',
        'summary': 'RTX 5090 Ventus OC 使用者安裝一個多月後，逐 pin 差異由約 1A 內逐步惡化；換四條線、改用 PSU 另一個 12V-2x6 端口仍無改善。WireView 完全插妥時仍有明顯晃動，移動裝置會讓不同 pin 變成 0A 或偏高，滿載時 Temp In 很快超過 80°C。拆除 WireView、把探頭貼在 GPU 端線材後，滿載最高約 64°C；Thermal Grizzly 因此寄送替換品。',
        'comments': 'der8auer 表示情況值得警覺並建議聯絡客服換貨；其他留言依序要求確認插妥、檢查 WireView 夾持端子及直接量測不經裝置的溫度。後續沒有替換品結果或實體檢驗，因此可確認裝置是此系統的高度疑點，不能寫成已證實的通用設計缺陷。',
        'url': 'https://www.reddit.com/r/ThermalGrizzly/comments/1t32e5j/wireview_pro_2_connection_overheating/'
    },
    {
        'date': '2026-03-29', 'source': 'Reddit', 'keyword': 'WireView',
        'match': '標題＋內文＋留言',
        'title': 'WireView Pro II extension cable with RTX 5090 FE',
        'summary': 'RTX 5090 FE 使用者因接頭方向需要延長線，詢問把 PSU 原生 12V-2x6、延長線與 WireView 串接是否增加風險。Thermal Grizzly 人員表示 WireView 仍能量測 PSU 到 GPU 的整段電流，且當時建議 FE 使用延長線。',
        'comments': '留言主要疑慮是三個接點增加故障介面，以及 ATX 3.0／3.1、PCIe 5.0／5.1 與 H+／H++ 標示混亂；有人主張應改用單一原生線，也有人回報 MODDIY 延長線搭配 WireView。官方並預告 Q2 2026 推出線材焊接版。這串顯示 FE／垂直安裝需要更少接點、規格標示更清楚的方案。',
        'url': 'https://www.reddit.com/r/ThermalGrizzly/comments/1s6za2f/wireview_pro_ii_extension_cable_with_5090fe/'
    },
    {
        'date': '2026-02-17', 'source': 'Reddit', 'keyword': 'WireView',
        'match': '標題＋內文＋留言',
        'title': 'AORUS P1200W to RTX 5090 with WireView current imbalance',
        'summary': 'RTX 5090／AORUS P1200W 使用者以顯示卡隨附轉接器搭配 WireView，約 47A 總電流時六路約 6–10A並反覆告警；他希望改用 PSU 直連線，減少接點並改善長期可靠性。',
        'comments': '留言多次建議重插各端與逐條推緊導線，有人表示多次重插後恢復。CableMod 回覆不支援此 PSU 的模組化直連線，也不建議在 5090 的既有轉接器後再加延長線；其他使用者回報同款線材第一條會觸發 pin 警報，第二條使用約三個月正常。這反映監控告警後仍缺少可驗證的相容線材與故障定位流程。',
        'url': 'https://www.reddit.com/r/ThermalGrizzly/comments/1r6t767/need_exact_cable_recommendation_aorus_p1200w_rtx/'
    },
])

# 2026 German-forum expansion. Each thread and its visible replies were read.
rows.extend([
    {
        'date': '2026-07-09', 'source': 'Hardwareluxx Forum', 'keyword': 'GPU Safeguard', 'match': '標題＋內文＋留言',
        'title': 'MSI MPG Ai1600TS im Test: mit GPU Safeguard+ gegen schmelzende 12V-2x6-Stecker',
        'summary': 'Hardwareluxx 的 Ai1600TS 評測串說明 PSU 以逐 pin 監控作為 Safeguard+ 核心；可見留言沒有提供故障注入或保護觸發結果。',
        'comments': '使用者主要質疑約 600 歐元售價及 1600W 對單 GPU 系統的必要性，也要求從 GPU 端根治接頭問題。這能確認價格與規格門檻，不能證明保護效果。',
        'url': 'https://www.hardwareluxx.de/community/threads/msi-mpg-ai1600ts-im-test-mit-gpu-safeguard-gegen-schmelzende-12v-2x6-stecker.1380494/'
    },
    {
        'date': '2026-06-24', 'source': 'ComputerBase Forum', 'keyword': 'ROG Equalizer', 'match': '標題＋內文＋留言',
        'title': 'ROG Equalizer 熔損圖片後續被確認為偽造',
        'summary': '討論串最初圍繞一張宣稱 ROG Equalizer 熔損的外部圖片；ComputerBase 編輯於 6 月 24 日更新，明確指出該圖片為偽造。',
        'comments': '前段留言已質疑圖片缺少硬體、負載與可核對來源；後續更正表示不能將該圖列為產品失敗案例。可確認的是未驗證事故圖會影響使用者信任。',
        'url': 'https://www.computerbase.de/forum/threads/asus-rog-equalizer-schmorstellen-am-kabel-sind-eine-faelschung.2273324/page-10'
    },
    {
        'date': '2026-06-08', 'source': 'ComputerBase Forum', 'keyword': 'WireView', 'match': '內文＋留言',
        'title': 'WireView II 新機型討論：無螢幕版本、主動均流與保護價值',
        'summary': 'Thermal Grizzly 新品串中，使用者討論無螢幕 WireView II 的外觀與定位，並比較 WireView 的監控／關機與 Ampinel 的主動均流。',
        'comments': '部分留言偏好較乾淨的無螢幕版本；也有人認為高價保護裝置應提供比風扇與顯示更多的主動處置。沒有新裝置觸發測試。',
        'url': 'https://www.computerbase.de/forum/threads/thermal-grizzly-erste-luefter-wireview-ii-eine-noctua-edition-und-tg-coating.2272904/page-2'
    },
    {
        'date': '2026-06-05', 'source': 'Hardwareluxx Forum', 'keyword': 'ThermalProtect', 'match': '標題＋內文＋留言',
        'title': 'ThermalProtect、PinProtect 與 PinProtect+ 的警示方式討論',
        'summary': '主文介紹 Corsair 三種 12V-2x6 保護方案；ThermalProtect 以線材溫度感測切斷 GPU 供電，PinProtect+ 則以軟體、PSU LED 與風扇轉速回報異常。',
        'comments': '留言認為只有紅色 LED 不容易被看見，要求直接的蜂鳴器；有人指出 GPU 斷電與 PSU 風扇全速本身也會形成訊號。討論沒有擁有者觸發案例。',
        'url': 'https://www.hardwareluxx.de/community/threads/thermalprotect-pinprotect-und-pinprotect-corsair-zeigt-schutzl%C3%B6sungen-f%C3%BCr-12v-2x6-problematik.1379683/'
    },
    {
        'date': '2026-05-22', 'source': 'ComputerBase Forum', 'keyword': 'Ampinel', 'match': '標題＋內文＋留言',
        'title': 'Ampinel 買家因相容性資訊變更辦理退貨',
        'summary': '買家表示下單後才看到更多顯示卡被加入不相容名單，自己的配置無法安心使用，因此把 Ampinel 退回；Aqua Computer 接受退貨。',
        'comments': '回覆指出水冷版 KFA2 4090 可安裝，但空冷背板可能干涉；討論要求可安裝清單、圖片與實際尺寸。這是機構相容性與資訊時效問題，不是保護功能失效。',
        'url': 'https://www.computerbase.de/forum/threads/aqua-computer-ampinel-12v-2x6-schutz-ab-16-00-uhr-fuer-100-euro-erhaeltlich.2265345/page-13'
    },
    {
        'date': '2026-05-05', 'source': 'Hardwareluxx Forum', 'keyword': 'GPU Safeguard', 'match': '型號＋內文＋留言',
        'title': 'MPG Ai1300TS 擁有者回報逐 pin 最大差約 0.3A',
        'summary': 'Ai1300TS 買家收貨後表示滿意，截圖中看到 12V-2x6 各 pin 最大差約 0.3A；這是單一系統的正常運作觀察。',
        'comments': '同一使用者之後回報 GPU 超過 800W 時沒有 coil whine，PSU 風扇最高約 650 RPM，日常遊戲約 350–400 RPM；沒有 Safeguard+ 告警、降載或關機紀錄。',
        'url': 'https://www.hardwareluxx.de/community/threads/mpg-ai1300ts-pcie5-release.1376483/'
    },
    {
        'date': '2026-04-30', 'source': 'Hardwareluxx Forum', 'keyword': 'ROG Equalizer', 'match': '標題＋內文＋留言',
        'title': 'ROG Equalizer 結構分析引發功能價值質疑',
        'summary': '討論串引用 ROG Equalizer 的 busbar 與強化端子分析；留言同時存在「品質較好的線材有價值」與「繞著接頭缺陷加產品」兩種看法。',
        'comments': '多名留言者表示 der8auer 的測試讓他們對均流效果保留態度，也有人認為 4090／5090 使用者仍會為降低風險購買。沒有長期或故障觸發數據。',
        'url': 'https://www.hardwareluxx.de/community/threads/rog-equalizer-12-v-br%C3%BCcke-und-dicke-kontakte-f%C3%BCr-mehr-sicherheit.1378749/'
    },
    {
        'date': '2026-04-29', 'source': 'ComputerBase Forum', 'keyword': 'ThermalProtect', 'match': '標題＋內文＋留言',
        'title': 'Corsair ThermalProtect：低價吸引力與感測位置疑問',
        'summary': '主文介紹 ThermalProtect 以線材內的溫度機制介入 sense pin；討論者推測其核心動作是偵測後切斷 sense pin，並要求進一步技術分析。',
        'comments': '留言認為約 18 歐元可接受；主要疑問是熱點是否只在接頭、距離接頭的感測點能否及時反應，以及 PSU 端風險是否未被覆蓋。沒有買家長期使用或誤報資料。',
        'url': 'https://www.computerbase.de/forum/threads/corsair-thermalprotect-kabel-zum-schutz-des-12v-2x6-anschlusses.2270488/'
    },
    {
        'date': '2026-04-28', 'source': 'Hardwareluxx Forum', 'keyword': 'ThermalProtect', 'match': '標題＋內文＋留言',
        'title': 'ThermalProtect 實測討論：65°C 觸發與間接測溫限制',
        'summary': 'Hardwareluxx 主文在 RTX 5090 Astral、約 600W 下以外部加熱讓 ThermalProtect 感測區達門檻，GPU 供電確實中斷；正常負載時接頭約 55.4°C，未自然觸發。',
        'comments': '留言集中質疑感測器距接頭約 30 mm、熱傳延遲與環境影響，也爭論外部測試方法是否足以代表局部高阻抗。這是媒體測試與技術討論，不等同一般使用者長期案例。',
        'url': 'https://www.hardwareluxx.de/community/threads/temperatur%C3%BCberwachung-mit-sense-eingriff-das-corsair-thermalprotect-600w-12v-2x6-kabel-ausprobiert.1378713/'
    },
    {
        'date': '2026-04-11', 'source': 'Hardwareluxx Forum', 'keyword': 'Titanload', 'match': '內文＋留言',
        'title': 'Titanload 與 Seasonic 線材的 600W／775–800W 紅外線溫度比較',
        'summary': 'RTX 5090 使用者以近新 Titanload 與 Seasonic 1600W Titanium 線材比較：先跑 600W 5 分鐘，再跑約 775–800W；短測時他估計 Titanload 低約 4–7°C。',
        'comments': '延長至約 40 分鐘後，發文者量到 PSU 端約 50–52°C、線材約 50°C、接頭約 51–52°C，GPU 端下側最熱約 60–63°C；他明確提醒斜角紅外線讀值受反射影響。這是單一系統比較。',
        'url': 'https://www.hardwareluxx.de/community/threads/offizieller-nvidia-rtx-5090-overclocking-und-modding-thread.1363289/page-141'
    },
    {
        'date': '2026-04-10', 'source': 'Hardwareluxx Forum', 'keyword': 'ROG Equalizer', 'match': '標題＋內文＋留言',
        'title': 'ROG Equalizer 極端斷線測試是否代表接觸不良情境',
        'summary': '主文轉述 ASUS 讓中間四條 12V 導體中斷、只由兩條供電的極端測試，宣稱強化線材能承受高電流。',
        'comments': '留言指出「完全斷路」不等同「未插妥或高接觸電阻」，並追問強化導體如何避免熱量在接點產生。這是測試設計質疑，不是實際熔損或保護成功案例。',
        'url': 'https://www.hardwareluxx.de/community/threads/schmelzende-12v-2x6-stecker-asus-rog-equalizer-kabel-h%C3%A4lt-in-extrem-situationen-durch.1378270/'
    },
    {
        'date': '2026-03-07', 'source': 'Hardwareluxx Forum', 'keyword': 'WireView', 'keywords': ['WireView', 'Ampinel'], 'match': '標題＋內文＋留言',
        'title': 'WireView Pro II 與 Ampinel 實務比較：相容性、均流、保固與軟體更新',
        'summary': 'Hardwareluxx 比較兩款轉接器後，留言補充 WireView 的 GPU 端插頭較長，對 MSI RTX 5090 Suprim 等卡較有機會相容；廠商回覆稱已檢查超過 70 張卡。',
        'comments': '使用者要求 inline 線材版、5090 FE 支援、清楚相容表與保固。對 Ampinel 的疑慮集中在主動均流、保固範圍與 AquaSuite 更新費；Aqua Computer 人員回覆均流可關閉。',
        'url': 'https://www.hardwareluxx.de/community/threads/%C3%9Cberwachung-und-regelung-des-12v-2x6-wireview-pro-ii-und-ampinel-im-praxisvergleich.1377308/page-2'
    },
    {
        'date': '2026-02-11', 'source': 'Hardwareluxx Forum', 'keyword': 'WireView', 'match': '標題＋內文＋留言',
        'title': 'WireView Pro II 韌體與軟體更新：使用者要求線材版與更佳相容性',
        'summary': '主文說明首版 Windows 軟體與韌體改善監控；一名擁有者表示從跨年起就在使用，並準備試用軟體。',
        'comments': '留言肯定廠商持續更新，但希望把裝置整合到線材中，減少凸出的轉接器並保留乾淨外觀；主要原因是部分顯示卡的機構相容性。沒有新的告警或故障定位案例。',
        'url': 'https://www.hardwareluxx.de/community/threads/wireview-pro-ii-tg-ver%C3%B6ffentlicht-neue-firmware-und-erste-software-version.1376493/'
    },
    {
        'date': '2026-02-09', 'source': 'ComputerBase Forum', 'keyword': 'WireView', 'match': '標題＋內文＋留言',
        'title': 'WireView Pro II 軟體使用回饋：介面、告警處置與已知問題',
        'summary': '討論串介紹 WireView Pro II Software 1.0.3；可見回覆確認可調整背景、具深色模式、保留 GPU 用電統計，並有使用者詢問告警後應重插還是直接換線。',
        'comments': '使用者批評交期長、軟體／韌體仍有 bug 與價格高；廠商列出的已知問題包含監控時 GPU 負載增加、全螢幕與特定 X870E＋HWiNFO USB 斷線。需求是明確告警處置與穩定、輕量軟體。',
        'url': 'https://www.computerbase.de/forum/threads/wireview-pro-ii-neue-firmware-und-software-mit-vielen-verbesserungen.2265325/'
    },
    {
        'date': '2026-01-21', 'source': 'ComputerBase Forum', 'keyword': 'WireView', 'match': '內文＋留言',
        'title': 'WireView Pro II 的 HWiNFO、Windows／Linux 與風扇使用疑問',
        'summary': '使用者確認 HWiNFO beta 能讀取 WireView Pro II，但當時仍需讓 WireView 軟體在背景執行；回覆指出官方 Windows 軟體之外，API／其他系統支援仍在規劃。',
        'comments': '留言也討論小風扇噪音、Normal／Reverse 方向與換卡後可否繼續使用；對靜音水冷系統，風扇可能成為拒買因素。這些是實際整合與選購疑慮，不是保護觸發資料。',
        'url': 'https://www.computerbase.de/forum/threads/thermal-grizzly-wireview-pro-ii-im-test-der-luxus-schutz-fuer-das-12v-2x6-stecker-problem.2263460/page-14'
    },
    {
        'date': '2026-01-08', 'source': 'ComputerBase Forum', 'keyword': 'GPU Safeguard', 'match': '標題＋內文＋留言',
        'title': 'GPU Safeguard+ 發表討論：認同主動保護，但質疑為接頭缺陷加價善後',
        'summary': 'ComputerBase 主文介紹 MSI PSU 的 GPU Safeguard+ 逐 pin 監控與主動保護；此串是發表討論，沒有擁有者觸發案例。',
        'comments': '留言認為 PSU 廠商願意加保護比放任熔損好，但批評這是替 12V-2x6 根本設計問題增加成本；也有人質疑監測究竟是每個 pin 或群組。',
        'url': 'https://www.computerbase.de/forum/threads/msi-netzteile-gpu-safeguard-schuetzt-vor-12v-2x6-steckerschaeden.2262806/'
    },
])

# 2026 English/German forum expansion. Each included thread was opened and its
# visible first post and replies were read; product claims remain separated from user observations.
rows.extend([
    {
        'date': '2026-06-12', 'source': 'Overclockers UK Forums', 'keyword': 'ROG Equalizer', 'match': '留言',
        'title': 'ROG Equalizer 實際使用後與 Corsair 線比較',
        'summary': '使用者表示已購買 ROG Equalizer，並與先前使用的約 £10 Corsair 線比較。',
        'comments': '該使用者回報溫度與各 pin 讀值沒有變化；另有留言詢問 90 度版本，回覆指出目前沒有消息。這是單一系統的使用比較，不是跨平台驗證。',
        'url': 'https://forums.overclockers.co.uk/threads/corsair-thermalprotect-rog-equalizer-enhanced-12v-2x6-cables.19012784/page-2'
    },
    {
        'date': '2026-04-29', 'source': 'Overclockers UK Forums', 'keyword': 'ThermalProtect', 'match': '標題＋內文＋留言',
        'title': 'CORSAIR ThermalProtect 與 ROG Equalizer 上市討論',
        'summary': '主文介紹 CORSAIR ThermalProtect 的 OTP 溫度感測切斷功能、原生 12V-2x6 相容性與約 £20 價格。',
        'comments': '使用者詢問 RMx 的 Type 4 版本、希望有 90 度接頭，並指出狹窄機殼可能形成過度彎折；另一名使用者等待測試，尚未提供 ThermalProtect 觸發結果。',
        'url': 'https://forums.overclockers.co.uk/threads/corsair-thermalprotect-rog-equalizer-enhanced-12v-2x6-cables.19012784/'
    },
    {
        'date': '2026-04-28', 'source': 'PC Games Hardware Extreme', 'keyword': 'ThermalProtect', 'match': '標題＋內文＋留言',
        'title': 'PCGH Extreme 討論 CORSAIR ThermalProtect：價格、相容性與感測位置',
        'summary': '主文說明 CORSAIR ThermalProtect 為帶整合式溫度保護的 12V-2x6 線材，建議售價 18 歐元。',
        'comments': '留言肯定低價，但詢問 Seasonic 等 PSU 的相容性；PCGH 回覆限定 PSU 與 GPU 兩端均為原生 12+4 接口時可用，專有 PSU 接口則不同。另有留言質疑若從外部加熱感測器，未必代表接頭熱點的實際保護能力，並指出它不能修復接點根因。',
        'url': 'https://extreme.pcgameshardware.de/threads/12v-2-6-kabel-mit-temperaturschutz-corsair-will-fuer-unter-20-euro-abhilfe-schaffen.674149/'
    },
    {
        'date': '2026-04-09', 'source': 'PC Games Hardware Extreme', 'keyword': 'ROG Equalizer', 'match': '標題＋內文＋留言',
        'title': 'PCGH Extreme 討論 ASUS ROG Equalizer 免費升級與技術內容',
        'summary': '主文說明 ROG Equalizer 以較均衡的供電與較低溫度降低 12V-2x6 風險，並提到 ASUS 提供升級方案。',
        'comments': '一名使用者回報其 Astral 系統待機 pin 差約 0.02A、負載差約 0.30A，且超頻時沒有達到 9A；另一名使用者質疑技術上實際改變了什麼，也有人希望改成統一標準。這些是個別系統讀值與意見。',
        'url': 'https://extreme.pcgameshardware.de/threads/12vhpwr-stecker-asus-rog-equalizer-soll-risiko-senken.673668/'
    },
    {
        'date': '2026-03-26', 'source': 'PC Games Hardware Extreme', 'keyword': 'GPU Safeguard', 'match': '標題＋內文＋留言',
        'title': 'PCGH Extreme 討論 MSI GPU Safeguard+ 的聲音警示',
        'summary': '主文說明 MSI GPU Safeguard+ 以 PSU 的聲音訊號提醒 12V-2x6 負載異常。',
        'comments': '使用者希望裝置不只發出聲音而能主動關機；另一人認為聲音警示不能取代均流，並有人指出已有一條線熔損、等待 Ampinel。也有 MSI MEG Ai1300P 擁有者表示自己的 PSU 沒有此功能，不想為此更換整台 PSU。',
        'url': 'https://extreme.pcgameshardware.de/threads/schmelzende-stromstecker-bei-gpus-msi-will-mit-hardware-alarmsignal-entgegensteuern.673250/'
    },
    {
        'date': '2026-03-24', 'source': 'PC Games Hardware Extreme', 'keyword': 'WireView', 'match': '標題＋內文＋留言',
        'title': 'WireView Pro II 找出使用近三年的缺接點線材',
        'summary': '使用者安裝 WireView Pro II 後發現一個 pin 完全沒有功率；拆查後確認隨 be quiet! DARK POWER 13 1000W 附帶的線材有一個 pin 沒有金屬接點。',
        'comments': '該系統顯示卡上限 450W，剩餘五條線仍在規格內，使用者表示近三年沒有察覺；原廠寄送替換線。留言討論裝機前目視檢查，但也指出這是個人案例，不能推算線材普遍失效率。',
        'url': 'https://extreme.pcgameshardware.de/threads/empfehlung-sichtpruefung-defekter-12vhpwr-stecker-hier-betroffen-be-quiet-dark-power-13-1000w.673185/'
    },
    {
        'date': '2026-02-26', 'source': 'PC Games Hardware Extreme', 'keyword': 'Ampinel', 'match': '標題＋內文＋留言',
        'title': 'Ampinel Retail 版 RTX 5090 安裝與初步測試',
        'summary': '使用者在 MSI RTX 5090 Gaming Trio OC 安裝 Ampinel Type B，展示顯示器、Aqua Suite 與 Cinebench／Furmark 測試。',
        'comments': '作者提醒下單前確認 Type A／B 方向及背板淨空；後續使用者回報 Type B 仍有約 3–4 mm 空間、標準 600W BIOS 超頻運作正常，但有一條線需要調整，且部分硬體監控軟體尚未支援。',
        'url': 'https://extreme.pcgameshardware.de/threads/rtx-5090-trifft-auf-aqua-computer-ampinel-retail-version-unboxing-einbau-und-ersteindruck.672373/'
    },
])

rows.extend([
    {
        'date': '2026-07-02', 'source': 'NGA玩家社區', 'keyword': 'ROG Equalizer', 'match': '標題＋內文＋留言',
        'title': 'ROG equalizer 399均流線現在老電源能打折',
        'summary': '發文者以 399 元價格討論 ROG Equalizer，表示看到網路燒損報導與「不均流」評測後，認為老電源搭配的購買價值可疑。',
        'comments': '留言出現「老電源能打折」與「賣不動盯上老韭菜」等負面價格評價；本串沒有提供實際測試數據。',
        'url': 'https://bbs.nga.cn/read.php?tid=47090177'
    },
    {
        'date': '2026-06-13', 'source': 'NGA玩家社區', 'keyword': 'ROG Equalizer', 'match': '標題＋內文＋留言',
        'title': 'rog 400塊的均流線燒了',
        'summary': '發文者回報 ROG 約 400 元均流線燒損，但未提供電源型號；主文認為只加強線材無法處理接頭本身。',
        'comments': '留言批評接口品質，討論端子鍍層與錫材接觸、線材機械應力；另有使用者分享其他 14A 線材在約 400W 時曾出現 160–180mV 壓降，換線後降至 40–80mV，但不能據此推論 ROG Equalizer 的普遍失效率。',
        'url': 'https://bbs.nga.cn/read.php?tid=46975741'
    },
    {
        'date': '2026-04-17', 'source': 'NGA玩家社區', 'keyword': 'GPU Safeguard', 'match': '標題＋內文＋留言',
        'title': '最近這是咋了，微星又出了內置電流均衡檢測的電源MPG Ai1300TS',
        'summary': '主文討論 MSI MPG Ai1300TS 內建電流均衡檢測；留言提到異常時可能先鳴叫約 3 分鐘後關機，也可能依電流差異直接關機。',
        'comments': '留言同時質疑 MSI 售後、價格、16A 插頭與 110V 相容性；另一則留言提到 SeaSonic OptiGuard，但本串沒有使用者觸發測試。',
        'url': 'https://bbs.nga.cn/read.php?tid=46586390'
    },
    {
        'date': '2026-01-08', 'source': 'NGA玩家社區', 'keyword': 'GPU Safeguard', 'match': '標題＋內文＋留言',
        'title': '[硬件產品討論] 阿龜星搞了個GPU Safeguard，過流強制斷電，以後就是黑屏星了',
        'summary': '主文描述 GPU Safeguard 在過流時先鳴叫，若未處理會強制切斷電源，並要求關機、拔下 12V-2x6 後檢查再重新插妥。',
        'comments': '留言擔心保護失效仍可能燒損、保固爭議、接頭插拔壽命與 3 分鐘延遲；有人希望電源提供雙 16-pin／雙 8-pin 路徑及 pin 電流回報。',
        'url': 'https://bbs.nga.cn/read.php?tid=45950741'
    },
    {
        'date': '2026-01-18', 'source': 'NGA玩家社區', 'keyword': 'WireView', 'match': '留言',
        'title': '5090線材燒接口相關',
        'summary': '發文者詢問 RTX 5090 與 1300W 電源的 12V-2x6 線材是否需要改用 14A 強流線。',
        'comments': '留言推薦一條國產監控線，並明確將其與 WireView Pro 作比較；本串沒有 WireView 實際量測數據。',
        'url': 'https://bbs.nga.cn/read.php?tid=46014425'
    },
    {
        'date': '2026-01-14', 'source': 'NGA玩家社區', 'keyword': 'WireView', 'match': '留言',
        'title': '請問5090燒接口的問題依然嚴重嗎？',
        'summary': '發文者詢問 RTX 5090 高負載與 12V-2x6 燒損風險，留言將 WireView Pro 與限制功耗列為處理方式。',
        'comments': '本串的 WireView Pro 內容是選購建議，沒有擁有者的 WireView 觸發或長期使用數據。',
        'url': 'https://bbs.nga.cn/read.php?tid=45988787'
    },
    {
        'date': '2026-07-20', 'source': 'Chiphell', 'keyword': 'ThermalProtect', 'match': '標題＋內文＋留言',
        'title': '【万恶老黄系列】贼船最近在做的12V-2x6（16Pin）防烧举措',
        'summary': '主文介紹 CORSAIR ThermalProtect：在線材靠近 GPU 端子處以熱敏元件偵測溫度，超過門檻後斷開 sense；同文也介紹 PSU 端 PinProtect／PinProtect+ 的過流切斷。',
        'comments': '留言認為接頭標準本身仍是問題，也有人希望其他廠商加入溫度感測；本串沒有使用者實際觸發測試。',
        'url': 'https://www.chiphell.com/thread-2849232-1-1.html'
    },
    {
        'date': '2026-07-16', 'source': 'Chiphell', 'keyword': 'ROG Equalizer', 'match': '標題＋內文＋留言',
        'title': '最終還是搞了一根ROG均流線，好硬！',
        'summary': '使用者在 ROG 電源與顯卡系統安裝 ROG Equalizer，實際感受是線材很硬，金屬環使 GPU 端延長並限制彎折角度。',
        'comments': '留言集中在安裝困難、側板空間與不同線材比較；直立顯卡較容易安裝，但沒有安全或溫升測試。',
        'url': 'https://www.chiphell.com/thread-2847439-1-1.html'
    },
    {
        'date': '2026-07-12', 'source': 'Chiphell', 'keyword': 'ROG Equalizer', 'match': '標題＋內文＋留言',
        'title': '華碩rog均流線海鮮那只要200出頭了',
        'summary': '主文討論 ROG Equalizer 二手／低價約 200 多元的取得方式，並推測可能是電源隨附線材。',
        'comments': '留言指出金屬環會增加長度並限制彎折，討論非 ASUS 電源相容性、真假與價格；沒有性能或保護測試。',
        'url': 'https://www.chiphell.com/thread-2845698-1-1.html'
    },
    {
        'date': '2026-07-08', 'source': 'Chiphell', 'keyword': 'ROG Equalizer', 'match': '標題＋內文＋留言',
        'title': 'ASUS ROG Equalizer大陆用户优惠券在小程序里申领',
        'summary': '主文是 ROG Equalizer 折價券活動，符合條件的 Thor III／Strix Platinum 買家最高可折半價。',
        'comments': '留言內容主要是申領資格與折扣，沒有產品安全、溫升或長期使用評價。',
        'url': 'https://www.chiphell.com/thread-2843303-1-1.html'
    },
    {
        'date': '2026-06-10', 'source': 'Chiphell', 'keyword': 'ROG Equalizer', 'match': '標題＋內文＋留言',
        'title': 'ROG Equalizer強流線已單獨銷售 自帶物理均流環，黑白同價399元',
        'summary': '主文介紹 ROG Equalizer 單獨銷售，標示 9.2A 提升至 17A、ATX3.1／PCIe5.1、黑白兩色與 399 元價格。',
        'comments': '留言質疑 der8auer 的批評與產品售價，出現「智商稅／信仰」等負面評價；沒有長期測試。',
        'url': 'https://www.chiphell.com/thread-2820215-1-1.html'
    },
    {
        'date': '2026-04-30', 'source': 'Chiphell', 'keyword': 'ROG Equalizer', 'match': '標題＋內文＋留言',
        'title': 'der8auer評測了一下ROG那个Equalizer强流线，有点难绷',
        'summary': '主文整理 der8auer 對 ROG Equalizer 的評測與疑慮。',
        'comments': '留言認為直接斷電過於強硬，偏好限制功耗；同時擔心電流不均與實際改善幅度。本串不是獨立重測。',
        'url': 'https://www.chiphell.com/thread-2802305-1-1.html'
    },
    {
        'date': '2026-04-29', 'source': 'Chiphell', 'keyword': 'ThermalProtect', 'match': '標題＋內文＋留言',
        'title': '海盜船推出內置OPT模組高溫斷電保護機制600W 12V-2x6線纜',
        'summary': '主文介紹 CORSAIR ThermalProtect 600W 12V-2x6 線材，OTP 模組距端子約 30mm，偵測到不安全溫度後關閉 GPU。',
        'comments': '留言認為多家廠商已有類似方案，但沒有提供實際觸發數據或長期使用結果。',
        'url': 'https://www.chiphell.com/thread-2802016-1-1.html'
    },
    {
        'date': '2026-04-10', 'source': 'Chiphell', 'keyword': 'ROG Equalizer', 'match': '標題＋內文＋留言',
        'title': '華碩推出ROG Equalizer強流線 單線承載能力提升至17A，自帶物理均流環',
        'summary': '主文以使用不當與老化造成電流不均為背景，介紹 ROG Equalizer 的金屬均流環、9.2A 至 17A 載流說法。',
        'comments': '留言討論線材綁定、價格與舊電源搭配；沒有長期使用測試。',
        'url': 'https://www.chiphell.com/thread-2795412-1-1.html'
    },
    {
        'date': '2026-04-01', 'source': 'Chiphell', 'keyword': 'GPU Safeguard', 'match': '標題＋內文＋留言',
        'title': '微星MAG A1200PLS PCIE5 戰斧導彈電源：次世代平台的穩定供電守護者',
        'summary': '主文介紹 MSI MAG A1200PLS 電源的 GPU 保護與 12V-2x6 供電設計。',
        'comments': '可見留言以致謝為主，沒有擁有者的觸發、溫升或長期使用測試。',
        'url': 'https://www.chiphell.com/thread-2792950-1-1.html'
    },
])

kw = ['WireView', 'GPU Safeguard', 'GPU Shield', 'OptiGuard', 'Ampinel', 'ROG Equalizer', 'GPU Tweak III Auto-Shutdown', 'Titanload', 'T-Guard', 'ThermalProtect', 'PinProtect／PinProtect+', 'TempGuard', 'EZDIY-FAB Alpha TS13', 'VGA 12+4PIN OCP Dongle']
keyword_info = {
    'WireView': (
        '逐針腳量測 12V-2x6 的電流，並監控電壓、溫度與功率；用於提早發現負載不均、接觸異常與過熱風險。',
        'Thermal Grizzly 官方資料',
        'https://www.thermal-grizzly.com/media/63/f8/a8/1773401971/TG_Datasheet_WV-P-2-W_EN_TGU20260313.pdf?ts=1773404845'
    ),
    'GPU Safeguard': (
        'MSI 電源供應器以智慧 IC 監控各針腳電流，偵測過載或不平衡並發出警示；Safeguard+ 可連動 MSI Afterburner 降低 GPU 功率。',
        'MSI 官方說明',
        'https://us.msi.com/blog/msi-gpu-safeguard-msi-afterburner-protect-your-gpu-by-reducing-power-during-abnormal-current'
    ),
    'GPU Shield': (
        'Cooler Master 以同一名稱提供兩種形式：獨立 GPU Shield Adapter Cable 串接於 PSU 與 GPU 之間，逐 pin 偵測異常電流並以 LED／蜂鳴器警示，嚴重異常時主動降低系統功耗；MWE Gold V4 則把 GPU Shield 智慧電流管理整合於 PSU。',
        'Cooler Master 官方產品頁',
        'https://www.coolermaster.com/en-in/products/gpu-shield-adapter.html'
    ),
    'OptiGuard': (
        'Seasonic 的 12V-2x6 GPU 保護方案，監測各端子電流及接頭附近溫度，以進行警示與保護。',
        'Seasonic 官方簡報',
        'https://investor.seasonic.com/wp-content/uploads/sites/3/2025/09/2025-0606-earnings-call-slideshow-zh.pdf'
    ),
    'Ampinel': (
        '以可控電阻平衡 12V-2x6 各路電壓降，藉此改善電流分配，並依接頭熱狀態調節；同時提供電流、電壓與連接品質分析。',
        'Aqua Computer 官方手冊',
        'https://aquacomputer.de/handbuecher.html?file=tl_files%2Faquacomputer%2Fdownloads%2Fmanuals%2FAMPINEL_en.pdf'
    ),
    'ROG Equalizer': (
        '以 GPU 端 busbar 連接六路電源接點，讓電流可在接頭端重新分配，並以強化端子提高載流餘裕；屬被動式設計，不會由軟體主動控制各路電流。',
        'ASUS ROG 官方頁面',
        'https://rog.asus.com/ca-en/power-supply-units/rog-equalizer/rog-equalizer/'
    ),
    'Titanload': (
        '採用較高載流能力的強電流端子，提高 12V-2x6 連接的電流餘裕並降低發熱；屬被動式強化線材。',
        '鑫谷官方發布',
        'https://www.bilibili.com/opus/1142077163208441927'
    ),
    'T-Guard': (
        'GIGABYTE 電源供應器的 12V-2x6 主動溫度監控與保護機制，用於偵測接頭過熱風險。',
        'GIGABYTE 官方新聞',
        'https://www.gigabyte.com/kr/press/news/2380'
    ),
    'ThermalProtect': (
        '在線材靠近 GPU 接頭處使用被動式溫度開關；達到門檻時改變感測針腳狀態，使 GPU 降低或停止取電，無需軟體。',
        'CORSAIR 官方技術說明',
        'https://www.corsair.com/us/en/explorer/diy-builder/power-supply-units/corsair-thermalprotect-technical-overview/'
    ),
    'PinProtect／PinProtect+': (
        '兩者皆整合於 CORSAIR 電源供應器，以逐 pin OCP 即時監控 12V-2x6 六路 +12V 電流，不偵測溫度。PinProtect 固定常駐，異常持續預設 30 秒後使 GPU 停止取電，畫面變黑且 PSU 風扇全速；PinProtect+ 另以 iCUE 顯示六路電流、警示與事件記錄，並可調整門檻及 10～180 秒延遲或停用。官方文章發布時，PinProtect 僅見於第二代 RM1200e，PinProtect+ 僅見於 HX1000i SHIFT CRYSTAL。',
        'CORSAIR 官方技術說明',
        'https://www.corsair.com/us/en/explorer/diy-builder/power-supply-units/what-is-pinprotect/'
    ),
    'TempGuard': (
        '以 GPU 端接頭內的 NTC 感測器監測溫度，並把訊號送回電源供應器執行安全保護。',
        'ASRock 官方產品頁',
        'https://www.asrock.com/Power-Supply/Taichi/TC-1300T/'
    ),
    'GPU Tweak III Auto-Shutdown': (
        'GPU Tweak III v2.1.8.0 起新增的選配功能：透過搭載 Power Detector+ 硬體的 ROG 顯示卡讀取 12V-2x6 六路逐 pin 電流，任一路電流持續高於約 12.5A 且超過使用者設定的觸發秒數（可調 1～5 分鐘）時關閉系統。僅追蹤此關機功能本身，不含 GPU Tweak III 軟體其餘超頻／風扇／RGB 等一般功能。功能預設關閉、需使用者手動啟用，且僅限少數搭載 Power Detector+ 的 ROG Astral／ROG Matrix 機型。',
        'ASUS ROG 官方技術說明',
        'https://rog-forum.asus.com/t5/technologies-explained/gpu-tweak-iii-v2-1-8-0-adds-power-detector-auto-shutdown/ba-p/1158169'
    ),
    'EZDIY-FAB Alpha TS13': (
        'U 型 12V-2x6 直通轉接器，內建 TFT 螢幕即時顯示 GPU 功耗與接頭溫度，無需搭配軟體；溫度超過 85°C 會發出警報。鋁合金外殼，標稱可支援 600W，提供黑／白兩色，並各有正向與翻轉（相容部分 ASUS 顯示卡接頭方向）版本。',
        'EZDIY-FAB 官方商品頁',
        'https://ezdiy-fab.com/collections/12v-2x6-adapter'
    ),
    'VGA 12+4PIN OCP Dongle': (
        '串接於電源線與顯示卡之間，逐路監控六條 +12V 電流。低於 9.5A 顯示正常 ARGB；9.5～12A 或任兩路差值超過 6A 且持續 10 秒時，以橘燈與短音警示；單路超過 12A 且持續 10 秒時，以紅燈與連續警報提示，180 秒後再倒數 15 秒觸發顯示卡黑畫面保護。官方未說明黑畫面保護的電路實作，也未宣稱監測溫度。',
        'Super Flower（振華）官方產品頁',
        'https://www.super-flower.com.tw/tw/products-detail/OCPD_M/'
    ),
}
keyword_category = {
    'WireView': 'GPU 端串接式監控／保護轉接器',
    'GPU Safeguard': '整合於 PSU 的逐 pin 電流監控與主動保護',
    'GPU Shield': '獨立 Adapter 線材／PSU 整合式異常電流保護',
    'OptiGuard': '整合於 PSU 的電流／溫度監控與保護系統',
    'Ampinel': 'GPU 端串接式主動電壓降平衡／監控轉接器',
    'ROG Equalizer': '12V-2x6 被動式強化／busbar 線材',
    'Titanload': '12V-2x6 高載流被動式強化線材',
    'T-Guard': '整合於 PSU 的接頭溫度監控／保護',
    'ThermalProtect': '內建被動溫度開關的 12V-2x6 線材',
    'PinProtect／PinProtect+': '整合於 PSU 的逐 pin 過流監控與主動保護',
    'TempGuard': 'PSU 專用溫度感測保護線材',
    'GPU Tweak III Auto-Shutdown': 'GPU Tweak III 軟體內選配的逐 pin 過流自動關機功能（僅此功能，非整套軟體）',
    'EZDIY-FAB Alpha TS13': 'GPU 端無軟體溫度／功耗顯示與警報轉接器',
    'VGA 12+4PIN OCP Dongle': 'GPU 端串接式逐線電流監控／警示轉接線',
}
product_form_factor = {
    'WireView': 'Adapter',
    'GPU Safeguard': 'PSU',
    'GPU Shield': 'Adapter 線材／PSU 整合功能',
    'OptiGuard': 'PSU',
    'Ampinel': 'Adapter',
    'ROG Equalizer': '線材',
    'Titanload': '線材',
    'T-Guard': 'PSU',
    'ThermalProtect': '線材',
    'PinProtect／PinProtect+': 'PSU',
    'TempGuard': '線材＋PSU',
    'GPU Tweak III Auto-Shutdown': '軟體功能',
    'EZDIY-FAB Alpha TS13': 'Adapter',
    'VGA 12+4PIN OCP Dongle': 'Adapter 線材',
}
product_detection = {
    'WireView': '電流＋溫度',
    'GPU Safeguard': '電流',
    'GPU Shield': '電流',
    'OptiGuard': '電流＋溫度',
    'Ampinel': '電流＋溫度',
    'ROG Equalizer': '無（被動均流）',
    'Titanload': '無（被動強化）',
    'T-Guard': '溫度',
    'ThermalProtect': '溫度',
    'PinProtect／PinProtect+': '電流',
    'TempGuard': '溫度',
    'GPU Tweak III Auto-Shutdown': '電流',
    'EZDIY-FAB Alpha TS13': '溫度＋功耗（非逐 pin 電流）',
    'VGA 12+4PIN OCP Dongle': '電流',
}
keyword_vendor = {
    'WireView': 'Thermal Grizzly',
    'GPU Safeguard': 'MSI',
    'GPU Shield': 'Cooler Master',
    'OptiGuard': 'Seasonic',
    'Ampinel': 'Aqua Computer',
    'ROG Equalizer': 'ASUS ROG',
    'Titanload': 'Segotep／鑫谷',
    'T-Guard': 'GIGABYTE',
    'ThermalProtect': 'CORSAIR',
    'PinProtect／PinProtect+': 'CORSAIR',
    'TempGuard': 'ASRock',
    'GPU Tweak III Auto-Shutdown': 'ASUS',
    'EZDIY-FAB Alpha TS13': 'EZDIY-FAB',
    'VGA 12+4PIN OCP Dongle': 'Super Flower（振華）',
}
# 產品功能／關鍵字功能表／使用者評價三個區塊改依品牌字母排序（不分大小寫）呈現；
# 這連帶決定第五節篩選晶片的關鍵字順序，讓全報告排序邏輯一致。
kw = sorted(kw, key=lambda k: keyword_vendor[k].lower())
product_display_names = {
    k: (
        'MSI GPU Safeguard+' if k == 'GPU Safeguard'
        else 'ASUS ROG Equalizer' if k == 'ROG Equalizer'
        else k if k == 'EZDIY-FAB Alpha TS13'
        else f'{vendor} {k}'
    )
    for k, vendor in keyword_vendor.items()
}
keyword_display_names = {
    k: ('GPU Safeguard+' if k == 'GPU Safeguard' else k)
    for k in kw
}
rows.extend([
    {
        'date': '2026-04-13', 'source': '百度貼吧／ROG手機吧', 'keyword': 'ROG Equalizer', 'match': '標題＋內文＋留言',
        'title': '華碩 ROG STRIX 白金雷鷹電源均流線版上市',
        'summary': '貼文介紹中國大陸上市的 ROG Equalizer 搭載版 ROG STRIX 白金雷鷹電源，涵蓋 850W 至 1200W、定價 1399～1899 元；補充文字宣稱線材為鍍錫實心無氧銅、GPU 端為加大鍍金觸點。',
        'comments': '可見留言只有產品補充說明，沒有擁有者的溫升、電流分配或長期使用測試；上述規格與性能數字屬貼文／補充文字，不列為使用者評價。',
        'url': 'https://tieba.baidu.com/p/10636501041'
    },
])

# 中國論壇常以「均流線／強流線」等功能稱呼取代英文產品名；以下均已核讀主文與可見留言。
rows.extend([
    {
        'date': '2026-08-08', 'source': 'Chiphell', 'keyword': 'Titanload', 'match': '標題＋內文＋留言',
        'title': '大佬們，想問個關於強流線的問題？',
        'summary': '發文者取得一條鑫谷強流線，詢問是否可搭配其他品牌、具原生 12V-2x6 接口的 ATX 3.1 電源，並比較 ASUS 額外 IVS 接口。',
        'comments': '一名自稱已購買鑫谷強流線的留言者把它描述為加粗線材、加長端子的被動強化方案；其他留言區分「強流線提高承載」與「均流線試圖改善分流」，並擔心線材無法處理 GPU 端接觸問題。另有一件不同品牌 16-pin 彎頭線無法插入特定電源的相容性回報，因此不能寫成跨品牌一定相容。',
        'url': 'https://www.chiphell.com/thread-2862733-1-1.html'
    },
    {
        'date': '2026-06-29', 'source': '百度貼吧／顯卡吧', 'keyword': 'ROG Equalizer', 'match': '標題＋內文＋留言',
        'title': 'AIDA64 為什麼識別不到顯卡功耗？',
        'summary': 'ROG RTX 5090 使用者搭配 ASUS 399 元均流線，回報部分開機後 AIDA64 與 MSI Afterburner 不顯示顯卡功耗，但 GPU-Z 可正常讀取。',
        'comments': '留言建議改用 HWiNFO、GPU-Z、GPU Tweak 或檢查 AIDA64 顯示設定與版本；發文者沒有回報最終根因，因此只能列為軟體讀值相容性疑問，不能判定由 ROG Equalizer 造成。',
        'url': 'https://tieba.baidu.com/p/10829530764'
    },
    {
        'date': '2026-06-15', 'source': 'Chiphell', 'keyword': 'ROG Equalizer', 'match': '標題＋內文＋留言',
        'title': '華碩 ROG 白金雷鷹 1000W EQUALIZER 均流線版開箱',
        'summary': '開箱文介紹隨 PSU 搭配的 ROG Equalizer、物理均流環、17A 與官方溫度數據；文中沒有同機對照或保護觸發測試。',
        'comments': '可見留言主要肯定外觀，也有人詢問是否優於訂製線、能否搭配其他品牌電源；沒有提供逐 pin、溫升或長期可靠性數據。',
        'url': 'https://www.chiphell.com/thread-2823885-1-1.html'
    },
    {
        'date': '2026-05-18', 'source': 'Chiphell', 'keyword': 'ROG Equalizer', 'match': '標題＋內文＋留言',
        'title': 'ROG STRIX 白金雷鷹 1000W 均流線版開箱',
        'summary': '開箱文整理 ROG Equalizer 的物理均流環、17A、IVS 與 GPU Tweak 資訊，並展示實際裝機外觀；沒有故障注入或前後對照量測。',
        'comments': '一名留言者直接質疑產品是否真的能均流；其他回覆多聚焦外觀、做工與模組線市場，不能當作保護效果證據。',
        'url': 'https://www.chiphell.com/thread-2809084-1-1.html'
    },
    {
        'date': '2026-05-09', 'source': 'NGA玩家社區', 'keyword': 'ROG Equalizer', 'match': '標題＋內文＋可見留言',
        'title': '華碩均流線國外 50 美元，國內真的 359？',
        'summary': '發文者討論中國售價，並轉述外部測試中兩個 pin 曾約為 9.8A 與 6.2A、相差接近 4A；本串沒有原始測試條件與完整記錄。',
        'comments': '一名擁有多顆 ROG PSU 的留言者表示原先可申請免費升級，但看到外部測試後暫緩；這能證實價格與第三方測試會影響購買意願，不能把轉述數字當成論壇使用者自行重測。',
        'url': 'https://bbs.nga.cn/read.php?tid=46741152'
    },
    {
        'date': '2026-04-15', 'source': 'Chiphell', 'keyword': 'ROG Equalizer', 'match': '標題＋內文＋留言',
        'title': 'ROG 雷神二代看來用不了均流線',
        'summary': '發文者原用 ROG Thor II 1200W 與 RTX 5090D，之後更換成 ROG STRIX 1200W 均流線版；回報電壓差由約 0.08–0.14V 降至約 0.04±0.005V，並表示接口溫度下降。',
        'comments': '同時更換了 PSU 與線材，滿載電壓亦由約 11.9V 變成約 11.8V，因此不能把差異全部歸因於 Equalizer。另一名高功耗使用者分享延長線因反覆插拔而從約 1A／20A 嚴重失衡，換線後改善；留言也質疑它應稱強流線而非主動均流。',
        'url': 'https://www.chiphell.com/thread-2797205-1-1.html'
    },
    {
        'date': '2026-04-13', 'source': 'NGA玩家社區', 'keyword': 'ROG Equalizer', 'match': '標題＋內文＋留言（2 頁）',
        'title': '華碩推出全新負載 17A 均流線',
        'summary': '主文介紹 ROG Equalizer 17A 與均流環，並反映年初購買 ROG Thor III 1600W 的使用者只能取得後續優惠、不能直接換線。',
        'comments': '留言集中質疑端子而非線徑才是風險核心、17A 如何驗證、均流環增加彎折空間，以及宣傳熱像是否呈現真正接頭熱點；後續有人引用外部不均流測試。這些是技術質疑與購買觀感，沒有論壇內獨立重測。',
        'url': 'https://bbs.nga.cn/read.php?tid=46564727'
    },
    {
        'date': '2026-04-13', 'source': 'Chiphell', 'keyword': 'ROG Equalizer', 'match': '標題＋內文＋留言',
        'title': 'ROG STRIX 白金雷鷹均流線版電源開售',
        'summary': '主文轉載 ROG Equalizer 強流線、17A、73.4°C 與中國售價資訊；數字來自產品發布資料，並非發文者測試。',
        'comments': '留言詢問技術是否會普及、線材是否只是加粗、老使用者換購政策與跨品牌相容性；另有人以「鞋小換鞋墊」質疑它沒有處理接頭根因。',
        'url': 'https://www.chiphell.com/thread-2796271-1-1.html'
    },
])

# 2026-08-19 weekly refresh: only threads whose visible post body and comments were read.
rows.extend([
    {
        'date': '2026-08-18', 'source': 'Reddit', 'keyword': 'WireView', 'match': '標題＋內文＋留言',
        'title': 'WireView Pro II 安裝後用壓力測試確認讀值穩定',
        'summary': 'RTX 5090 使用者因顯示卡價格與 12V-2x6 風險購入 WireView Pro II，主要看重 soft／hard shutdown；安裝後執行約 20 分鐘 FurMark，並玩數款遊戲，表示各 pin 沒有出現明顯異常差距。',
        'comments': '一名留言者表示原 Corsair 線材曾顯示嚴重不均，換線後讀值恢復；發文者因此認為監控能提早發現線材問題。這是兩名使用者的觀察，沒有提供完整逐 pin 原始數據，也沒有實際保護觸發。',
        'url': 'https://www.reddit.com/r/ThermalGrizzly/comments/1vrjtee/wire_view_pro_2_installed_and_can_now_sleep_a/'
    },
    {
        'date': '2026-08-18', 'source': 'Reddit', 'keyword': 'WireView', 'match': '標題＋內文＋留言',
        'title': 'WireView Pro II 在特定遊戲啟動時出現 pin 波動',
        'summary': 'RTX 5090 使用者表示只有啟動 Spider-Man 2 時，各 pin 電流會明顯波動且第 6 pin 常偏高；FurMark 測試則正常，因而詢問是否應重新插接。',
        'comments': '留言建議先確認是否真的觸發告警，再重插 GPU／PSU 兩端或換線；也有人認為遊戲設定、V-Sync 或瞬時負載可能造成波動。討論沒有最終診斷，不能判定為接頭故障或產品誤報。',
        'url': 'https://www.reddit.com/r/ThermalGrizzly/comments/1vr97za/wireview_2_imbalance_on_5090_only_when_booting_up/'
    },
    {
        'date': '2026-08-18', 'source': 'TechPowerUp Forums', 'keyword': 'ThermalProtect', 'match': '標題＋內文＋留言',
        'title': 'Corsair 2026 RMe Platinum PSU 搭載 ThermalProtect 線材',
        'summary': '主文介紹 RM850e／RM1000e Platinum 隨附 ThermalProtect：保護模組位於 GPU 接頭約 30 mm 處，線材溫度超過 65°C 時透過 sense pin 使 GPU 關閉；此為產品發布資訊，不是論壇獨立測試。',
        'comments': '留言焦點是 65°C 門檻是否過低、短暫尖峰會否觸發、距接頭約 30 mm 能否及時反映局部熱點，以及展示圖的彎折方式。一名實際買家肯定線材柔軟度與品質，但仍不建議大幅彎折；另一名留言者引用技術頁指出它是雙金屬開關。沒有新的實際關機觸發案例。',
        'url': 'https://www.techpowerup.com/forums/threads/corsair-launches-the-2026-rme-series-platinum-psus-with-thermalprotect-12v-2x6-cables.351686/'
    },
    {
        'date': '2026-08-17', 'source': 'Reddit', 'keyword': 'ROG Equalizer', 'match': '標題＋內文＋留言',
        'title': 'RTX 5080 使用者比較 12V-2x6 保護方案',
        'summary': '發文者因 12V-2x6 熔損風險詢問 WireView、Ampinel、ASUS ROG Equalizer、MSI GPU Safeguard+ 與 Corsair PinProtect+ 是否真正有效，並表示看過影片留言後對 Equalizer 的信任下降。',
        'comments': '留言普遍強調正確插接、原生 PSU 線材與避免過度彎折；部分人認為內建 PSU／GPU 的逐 pin 監控較完整，外接監控器會增加兩組接點，也有人重視 WireView 的關機與延長保固。另有留言質疑單點溫度感測能否及時發現單 pin 熱點。全串是方案比較與風險觀感，沒有同機受控實測。',
        'url': 'https://www.reddit.com/r/LinusTechTips/comments/1vqt4vi/regarding_melting_12vhpwr_power_cables_for_nvidia/'
    },
    {
        'date': '2026-08-16', 'source': 'Reddit', 'keyword': 'WireView', 'match': '標題＋內文＋留言',
        'title': 'Reverse WireView Pro II 顯示正常但顯卡未供電',
        'summary': 'ASUS TUF RTX 5090 OC 使用者安裝 reverse WireView Pro II 後，裝置螢幕可亮但顯卡不啟動；移除 WireView 後顯卡可正常供電。系統使用較舊、沒有原生 16-pin 的 PSU 與四路轉接線。',
        'comments': '留言要求補充安裝照片，並建議改用 PSU 原生線材或 ATX 3.1 PSU。發文者沒有回報最終根因，因此只能列為相容性／安裝疑問，不能判定 WireView 本體故障。',
        'url': 'https://www.reddit.com/r/ThermalGrizzly/comments/1vpfehf/wire_view_pro_ii_asus_rog_5090_tuf_oc_not_working/'
    },
    {
        'date': '2026-08-16', 'source': 'ComputerBase Forum', 'keyword': 'WireView', 'match': '內文＋留言',
        'title': 'RTX 5090 組裝討論中的 WireView Pro II 長期使用回報',
        'summary': '一名 ASUS TUF RTX 5090 使用者表示自 2025 年 12 月起搭配 WireView Pro II，系統維持安靜，並把硬體監控視為顯卡的額外保護。',
        'comments': '可見回覆沒有提供逐 pin、溫度、告警或實際關機紀錄，因此只可視為約八個月的正向持有經驗，不能證明保護曾成功觸發。',
        'url': 'https://www.computerbase.de/forum/threads/absegnung-5090-build.2276718/page-3'
    },
    {
        'date': '2026-08-15', 'source': 'Reddit', 'keyword': 'GPU Shield', 'match': '標題＋內文＋留言',
        'title': 'RTX 5080 組裝者比較具 per-pin OCP 的 PSU',
        'summary': 'RTX 5080／9950X3D 組裝者詢問是否需要 per-pin OCP，並比較 MSI、ASUS 與 Cooler Master MWE Gold V4 GPU Shield 等方案。',
        'comments': '一名 MWE V4 擁有者表示因相關評測很少，最後依產品所述的「過流先降載、持續過流再關機」邏輯選購；他沒有遇到或測試實際觸發。這能反映購買理由與評測缺口，不能當成保護效果驗證。',
        'url': 'https://www.reddit.com/r/buildapc/comments/1volf7s/per_pin_ocp_psu_vs_none/'
    },
    {
        'date': '2026-08-14', 'source': 'Reddit', 'keyword': 'Ampinel', 'match': '標題＋內文＋留言',
        'title': '全新 Ampinel Rev.4 外觀殘膠與版本疑慮',
        'summary': '買家收到全新 Ampinel Rev.4，發現 12VHPWR 接頭周圍有明顯殘膠；朋友先前的 Rev.4 曾出現 pin balancing 問題並換成 Rev.5，因此詢問是否應直接使用或先聯絡原廠。',
        'comments': '留言對 Ampinel 與 WireView 的優劣意見分歧；有人看重 Ampinel 的主動均流、被動散熱、價格與 AquaSuite，也有人強調均流不能修復物理接觸不良。另有使用者以 WireView Pro II、ThermalProtect 與 HWiNFO 指令組成多層關機保護。全串沒有確認殘膠是否影響功能，也沒有發文者後續處理結果。',
        'url': 'https://www.reddit.com/r/watercooling/comments/1vo2wsd/is_this_something_ideal_to_look_on_brand_new/'
    },
])

# NGA uses 「顯卡衛士」 as the common local name for Cooler Master GPU Shield.
rows.extend([
    {
        'date': '2026-08-14', 'source': 'NGA玩家社區', 'keyword': 'GPU Shield', 'match': '標題＋內文＋留言',
        'title': 'Cooler Master GPU Shield 實裝：機殼空間不足可能放不下',
        'summary': '首批買家以照片分享 GPU Shield 實裝，直接指出裝置與線材占用空間大，機殼若沒有足夠底部空間便難以安置；本串沒有實際過流或關機測試。',
        'comments': '留言認為中／全塔較容易安裝，也有人質疑裝置處理的是過流而非接觸電阻根因。其餘大量留言在討論機殼與散熱，不能當成 GPU Shield 效果評價。',
        'url': 'https://bbs.nga.cn/read.php?tid=47371845'
    },
    {
        'date': '2026-08-13', 'source': 'NGA玩家社區', 'keyword': 'GPU Shield', 'match': '主文＋留言（3 頁）',
        'title': 'RTX 5090 燒接口轉載討論中的 GPU Shield／Safeguard+ 選擇',
        'summary': '主文轉載一件 RTX 5090 與長城 F12 線材燒損案例，表示顯卡仍可使用、之後送修並更換 PSU；這是外部影片轉述，論壇沒有原始量測，不能據此判定事故根因。',
        'comments': '一則獲 13 個支持的留言把 Cooler Master「顯卡衛士」與 MSI 具電流警報的 PSU 列為較穩妥方案；後續使用者看重 MSI 與 Afterburner 的監控、警報及自動降功率，也有人因其他品牌保固限制而考慮 GPU Shield 轉接線。這些是選購與功能認知，沒有保護觸發實測。',
        'url': 'https://bbs.nga.cn/read.php?tid=47361387'
    },
    {
        'date': '2026-08-12', 'source': 'NGA玩家社區', 'keyword': 'GPU Shield', 'match': '標題＋內文＋留言',
        'title': 'Cooler Master GPU Shield 到貨安裝：線材過硬且側板空間吃緊',
        'summary': '買家收到 GPU Shield 後回報說明書限制安裝方向，實裝時線材非常硬，關閉玻璃側板需要壓線並反覆調整位置；他原本以為也能安裝在 PSU 端，但說明書不允許。',
        'comments': '留言把約 359 元價格、三年保障與發票／購買證明視為購買考量；有人期待單 pin 過流自動斷電，也有人只把它當成高價顯卡的額外保險。全串沒有實際告警、斷電或熔損後理賠紀錄。',
        'url': 'https://bbs.nga.cn/read.php?tid=47355461'
    },
    {
        'date': '2026-08-12', 'source': 'NGA玩家社區', 'keyword': 'GPU Shield', 'match': '標題＋內文＋留言',
        'title': 'Cooler Master GPU Shield 首批到貨：尺寸、重量與供貨疑慮',
        'summary': '另一名首批買家展示 GPU Shield 轉接盒與線材，主要負面感受是包裝相對過大、線材很長且外觀不佳；發文當下尚未提供上機後的保護測試。',
        'comments': '留言擔心裝置重量下墜影響接頭穩定，認為需要放在機殼底部平台；也反映缺少短線版本、自營平台缺貨、約 337～359 元價格、跨品牌 PSU 相容性及「若仍燒損由誰負責」的疑問。',
        'url': 'https://bbs.nga.cn/read.php?tid=47354624'
    },
    {
        'date': '2026-08-10', 'source': 'NGA玩家社區', 'keyword': 'GPU Shield', 'match': '標題＋內文＋留言',
        'title': 'Cooler Master GPU Shield Adapter「顯卡衛士」上市討論',
        'summary': '主文分享 Cooler Master GPU Shield Adapter 中國通路頁，將其描述為即插即用的顯卡防熔損保護；主文沒有自行測試產品效果。',
        'comments': '留言認為高價顯卡存在購買需求，但集中質疑約 359 元價格、三年保障、額外轉接接點、線材彎折、硬質外殼與中塔機殼淨空。另有使用者希望能讀取六路電流，也有人偏好直接使用溫度探頭與自動降功率。',
        'url': 'https://bbs.nga.cn/read.php?tid=47343776'
    },
])

# CORSAIR PinProtect／PinProtect+ 專項補查：官方功能另列於關鍵字說明；以下明細只整理
# 已完整讀取主文與可見留言的論壇內容，沒有把產品發布宣稱當成擁有者實測。
rows.extend([
    {
        'date': '2026-10-25', 'source': 'Reddit', 'keyword': 'PinProtect／PinProtect+',
        'keywords': ['PinProtect／PinProtect+'], 'match': '標題＋內文＋留言',
        'title': 'New RMe PSU with 12V-2x6 per-pin overcurrent protection?',
        'summary': '買家因第二代 RM1200e 的 PinProtect 逐 pin OCP 下單白色版，但 Amazon／Newegg 仍同時列出 2023、2025 等同名 RM1200e，產品頁也未必標示 PinProtect，造成新舊代辨識困難；CORSAIR 官網當時顯示延至 11 月出貨。',
        'comments': '發文者下單時看到 204.99 美元，數小時後頁面變成 279.99 美元，並質疑價格變動。CORSAIR 人員 -jonnyGURU- 說明第二代 PinProtect 版料號為 CP-9020316-XX（黑）與 CP-9020317-XX（白），舊代沒有 PinProtect；留言確認發文者買到正確料號，也認為通路的年份命名增加混淆。本串沒有實際保護觸發或長期使用資料。',
        'url': 'https://www.reddit.com/r/Corsair/comments/1xdndw4/new_rme_psu_with_12v2x6_perpin_overcurrent/'
    },
    {
        'date': '2026-10-21', 'source': 'TechPowerUp Forums', 'keyword': 'PinProtect／PinProtect+',
        'keywords': ['PinProtect／PinProtect+'], 'match': '標題＋內文＋留言',
        'title': 'Corsair Launches RM1200e Power Supply with Built-in PinProtect GPU OCP',
        'summary': '主文介紹第二代 RM1200e 的 PinProtect：PSU 端即時監控六路 +12V 電流，若單路電流長時間超過預設門檻便降低 GPU 線材供電並使顯示卡關閉；另附雙色接頭、黑白兩色與 10 年保固。這是產品發布資訊，不是論壇獨立測試。',
        'comments': '留言者認為逐 pin OCP 比只監控線材溫度更完整，但也希望能同時監控 GPU 端；多則留言批評消費者必須為接頭設計風險額外更換電源，並擔心未搭載保護的 PSU 日後更容易被歸責為使用者問題或產生保固爭議。沒有 RM1200e 擁有者回報實際觸發。',
        'url': 'https://www.techpowerup.com/forums/threads/corsair-launches-rm1200e-power-supply-with-built-in-pinprotect-gpu-ocp.353971/'
    },
    {
        'date': '2026-10-19', 'source': 'Reddit', 'keyword': 'PinProtect／PinProtect+',
        'keywords': ['PinProtect／PinProtect+', 'WireView', 'GPU Safeguard', 'GPU Shield', 'Ampinel'],
        'match': '標題＋內文＋留言',
        'title': 'What’s the latest on 12V GPU connectors?',
        'summary': '發文者詢問 12V GPU 接頭是否仍會熔損，以及是否已有萬無一失的解法；主文沒有自己的故障案例。',
        'comments': '一名留言者認為高功耗 GPU 應優先選擇內建逐 pin 電流監控的 MSI GPU Safeguard+ 或 CORSAIR PinProtect+，理由是 WireView／Ampinel 類外接監控器會增加兩個 12V-2x6 接頭；其他留言則推薦 WireView、GPU Shield、原生 ATX 3.1 線材或避免高功耗型號。這些是選購意見，沒有 PinProtect／PinProtect+ 實際觸發，也沒有形成一致結論。',
        'url': 'https://www.reddit.com/r/buildapc/comments/1x9km8a/whats_the_latest_on_12v_gpu_connectors/'
    },
    {
        'date': '2026-06-02', 'source': 'ComputerBase Forum', 'keyword': 'PinProtect／PinProtect+',
        'keywords': ['PinProtect／PinProtect+', 'ThermalProtect'], 'match': '標題＋內文＋留言',
        'title': 'Corsair AXi、HXi、RMe 的 12V-2x6 保護討論',
        'summary': '主文介紹 CORSAIR 在 PSU 內導入 PinProtect／PinProtect+ 逐 pin 過流保護，以及 ThermalProtect 溫度保護線材；論壇共兩頁、32 則留言已讀。',
        'comments': '有留言肯定 iCUE 可讀取資料，但更多人批評以 PSU 保護彌補接頭根本問題；技術討論指出 PSU 端逐線電流可作為接觸異常訊號，卻不能直接量到 GPU 接頭局部熱點。另有留言擔心保護切斷會造成遊戲中斷或未儲存資料遺失，希望在斷電前先警示，並質疑旗艦 AX 型號為何沒有 PinProtect+。本串沒有擁有者觸發案例。',
        'url': 'https://www.computerbase.de/forum/threads/corsair-axi-hxi-und-rme-netzteile-schuetzen-12v-2x6-anschluss.2272561/'
    },
])

keyword_search_aliases = {
    'WireView': 'WireView、Wire View、WireView Pro／Pro II、WireView II、暴力熊、顯卡功耗監測器、GPU 電源監視器、逐 pin／單 pin 電流監控',
    'GPU Safeguard': 'GPU Safeguard／Safeguard+、微星顯卡保護、逐 pin 電流監測、過流警報／強制斷電、MPG Ai1600TS／Ai1300TS、MEG Ai1600T／Ai1300P／Ai1000P、per-pin current、PSU telemetry、Prometheus／Grafana',
    'GPU Shield': 'GPU Shield、GPU Shield Adapter、MWE Gold V4、酷冷顯卡衛士／顯卡保護連接器、防熔斷保護、獨立 GPU Shield 連接器',
    'OptiGuard': 'OptiGuard、海韻顯卡保護、逐針電流／溫度監控、PRIME ENTERPRISE TX／PX',
    'Ampinel': 'Ampinel、智慧型 12V-2x6 轉接器、主動均流、負載均衡轉接器',
    'ROG Equalizer': 'ROG Equalizer、ASUS Equalizer、均流線、強流線、ROG EQ 顯卡模組線、物理均流環',
    'Titanload': 'Titanload、Segotep Titanload、鑫谷強流線、14A 強流線、TITANLOAD 強流線',
    'T-Guard': 'T-Guard、GIGABYTE T-Guard、技嘉主動熱監控、12V-2x6 熱敏保護',
    'ThermalProtect': 'ThermalProtect、Thermal Protect、CORSAIR ThermalProtect、海盜船溫控保護線、OTP 高溫保護線、防燒線',
    'PinProtect／PinProtect+': 'PinProtect、PinProtect+、Pin Protect、CORSAIR PinProtect、per-pin OCP、逐 pin／單 pin 過流保護、海盜船逐針腳電流監控、RM1200e Gen 2、CP-9020316／CP-9020317、HX1000i SHIFT CRYSTAL',
    'TempGuard': 'TempGuard、ASRock TempGuard；Taichi TC-1650T／TC-1300T／TC-3000P；Phantom Gaming PG-1600G／PG-1300G／PG-1000G／PG-850G／PG-750G／PG-1000PSF／PG-850PSF；Steel Legend SL-1200P／SL-1000P／SL-850P；CB-12V2X6L600W／90-UCX060-71XCAB；NTC sensor／temperature sensor／thermistor／Heißleiter、auto shutoff／cable over-temperature protection、華擎溫度保護線、熱敏保護線、高溫斷電；另以 ASRock＋完整 PSU／線材型號＋12V-2x6＋melted／smoking／arcing 交叉查找未寫產品名的事故文',
    'GPU Tweak III Auto-Shutdown': 'GPU Tweak III auto-shutdown、GPU Tweak III shutdown、Power Detector+ auto-shutdown、Power Detector+ shutdown、ROG Astral／ROG Matrix per-pin shutdown、12.5A 過流保護；注意：純粹的 GPU Tweak III 超頻／風扇／RGB 相關討論不算命中，須同時提到過流關機／Power Detector+ 才納入',
    'EZDIY-FAB Alpha TS13': 'EZDIY-FAB Alpha TS13、EZDIY-FAB 12V-2x6 adapter、Alpha TS13、EZDIY 溫度顯示轉接器',
    'VGA 12+4PIN OCP Dongle': 'VGA 12+4PIN 過電流保護轉接線、VGA 12+4PIN OCP Dongle、Super Flower OCP Dongle、振華 OCP 轉接線、振華顯卡過流保護轉接線',
}
reddit_required_query_lanes = (
    '產品全名與別名（Relevance＋New）',
    '廠牌＋完整 PSU／線材型號（Relevance＋New）',
    '廠牌＋保護功能描述（per-pin／temperature sensor／auto shutoff）',
    '12V-2x6／12VHPWR＋事故詞（melted／burnt／smoking／arcing）',
    'Comments 分頁',
)
reddit_discovery_audit = [
    ('MSI MPG Ai1600TS', 'https://www.reddit.com/r/MSI_Gaming/comments/1u3njt8/review_msi_mpg_ai1600_ts_pcie5_psu_review/', '納入', 'Safeguard+ 安裝與設定留言'),
    ('MSI MPG Ai1600TS', 'https://www.reddit.com/r/buildapc/comments/1uoypxa/need_some_advise_on_the_new_msi_mpg_ai1300_ts/', '納入', '因 Safeguard+ 產生的購買比較'),
    ('MSI MPG Ai1600TS', 'https://www.reddit.com/r/MSI_Gaming/comments/1ur8ybe/avoid_msi_ai1600ts_if_you_when_something_silent/', '納入', '產品可靠性及 OptiGuard 轉換意向'),
    ('MSI MPG Ai1600TS', 'https://www.reddit.com/r/MSI_Gaming/comments/1uwzpqn/msi_mpg_ai1300ts_12v_wattage_reading_seems_way/', '納入', '逐 pin 與主 rail telemetry 判讀'),
    ('MSI MPG Ai1600TS', 'https://www.reddit.com/r/MSI_Gaming/comments/1uxj6a2/msi_mpg_ai1600ts_perpin_current_monitoring_i/', '納入', '逐 pin Linux／Prometheus 工具'),
    ('MSI MPG Ai1600TS', 'https://www.reddit.com/r/PcBuild/comments/1skbkld/are_there_any_reviews_about_the_new_msi_psus_msi/', '排除', '一般購買詢問，可見內容未提供 Safeguard 實測或新增功能證據'),
    ('MSI MPG Ai1600TS', 'https://www.reddit.com/r/MSI_Gaming/comments/1su0hfu/the_msi_ai1600ts_is_too_noisy/', '排除', '噪音個案已由內容更完整且有原廠回應的同型號討論涵蓋'),
    ('ROG Equalizer／WireView', 'https://www.reddit.com/r/ThermalGrizzly/comments/1wi53nd/update_post_rog_equalizer_with_wvp_2/', '納入', 'RTX 5080 pin 電流、溫度與 bridge 前後監控範圍留言'),
    ('ROG Equalizer／WireView', 'https://www.reddit.com/r/ThermalGrizzly/comments/1whd8yh/wireview_pro_2_and_rog_equalizer/', '納入', 'Thermal Grizzly 回覆監控邊界及使用者接頭／故障疑慮'),
    ('GPU Safeguard', 'https://www.reddit.com/r/watercooling/comments/1wihia6/rtx_5090_owners_worth_upgrading_to_a/', '納入', 'MSI MPG Ai1300TS 買家說明整合式 per-pin 監控的選購理由'),
    ('WireView', 'https://www.reddit.com/r/ThermalGrizzly/comments/1wi64cq/wireview_pro_ii_thermals_question/', '納入', '高功耗水冷系統 WireView IN／OUT 溫度與 pin 讀值'),
    ('WireView', 'https://www.reddit.com/r/ThermalGrizzly/comments/1wlzsav/gigabyte_rtx_4090_windforce_wireview_pro_2/', '納入', 'RTX 4090 與 Wired 版相容性回覆'),
    ('GPU Safeguard／Ampinel／WireView', 'https://www.reddit.com/r/gpu/comments/1wfcl7m/whats_currently_the_best_option_for_protecting_a/', '納入', '使用者比較外接監控／主動均流／整合式 PSU 的選擇與疑慮'),
    ('WireView', 'https://www.reddit.com/r/ThermalGrizzly/comments/1wsukcp/wireview_pro_ii_6_wire_monitoring_gap/', '納入', '6 條 +12V 監控範圍與接地回流說明'),
    ('WireView', 'https://www.reddit.com/r/ThermalGrizzly/comments/1wsh3dj/going_from_regular_wv_pro_2_to_noctua_edition/', '納入', '一般版升級 Noctua Edition 的價格與風扇疑慮'),
    ('WireView', 'https://www.reddit.com/r/ThermalGrizzly/comments/1wrh7l1/wireview_pro_ii_gpu_noctua_edition_is_here/', '納入', 'Noctua Edition 上市、風扇、Wired 版與相容性留言'),
    ('WireView', 'https://www.reddit.com/r/ThermalGrizzly/comments/1wrt3eg/is_there_a_way_to_replace_the_fan/', '納入', '風扇磨擦聲、客服更換與拆解教學'),
    ('WireView', 'https://www.reddit.com/r/ThermalGrizzly/comments/1wrwyo9/which_version_to_get/', '納入', '垂直安裝時的版本與機殼路徑相容性'),
    ('OptiGuard', 'https://www.reddit.com/r/nvidia/comments/1wp9dx4/rtx_5090_12v2x6_connector_reaches_917c_with_dlss/', '納入', '91.7°C 接頭事件中的個人推薦，無 OptiGuard 實測'),
    ('PinProtect', 'https://www.reddit.com/r/Corsair/comments/1xdndw4/new_rme_psu_with_12v2x6_perpin_overcurrent/', '納入', '第二代 RM1200e 料號、價格與供貨辨識；完整可見留言已讀'),
    ('PinProtect+／GPU Safeguard+／WireView／GPU Shield／Ampinel', 'https://www.reddit.com/r/buildapc/comments/1x9km8a/whats_the_latest_on_12v_gpu_connectors/', '納入', '整合式 PSU 與外接監控器的接頭數量及選購比較；完整可見留言已讀'),
]
pm_info = {
    'WireView': (
        '可查看功率、溫度與各 pin 電流；已有告警後找到退縮 pin／故障線材，以及 Wired 版自動關機支援無人 AI 工作負載的案例。',
        '只監控、不修正接點劣化；增加額外接頭、重量與插拔風險。另有裝置熔損、告警後處理不清、安裝相容性、價格，以及軟體常駐造成約 30% FPS 損失的使用者回報。',
        '把告警轉成分步診斷與 RMA 流程；提供分級降功率／關機、離線事件記錄及輕量軟體；改善接頭壽命、低高度支架、GPU 適配表與量測精度公開。',
        '多則實際使用，正負案例皆有',
        'https://www.reddit.com/r/ThermalGrizzly/comments/1v0uzle/wire_view_2_software_causes_huge_performance/'
    ),
    'GPU Safeguard': (
        '使用者重視 per-pin 電流監控、可設定門檻及自動降載；有留言描述約 3 秒內載入 Afterburner profile，將每 pin 電流由 9A 以上降到約 4–6A。',
        '價格與供貨是主要阻力；另有 Windows／MSI Center、USB 安全、量測精度、效率與故障後需重新開機才能讀記錄的疑慮。使用者仍認為它是在替接頭根因善後。',
        '保留硬體獨立保護並提供跨平台設定；公開預設門檻、精度及反應時間；加入斷電後可讀的非揮發記錄，並下放到約 1000W／250 美元級距。',
        '多則設定與購買評價；自動降載為使用者敘述',
        'https://www.techpowerup.com/forums/threads/msi-mpg-ai1600ts.346215/'
    ),
    'GPU Shield': (
        '有留言認為使用者可能願意購買具保護功能的 PSU，保護高價顯示卡。',
        'TechPowerUp 的 7 則留言主要把它視為接頭缺陷衍生的補救產品，且直接比較競品；本期仍沒有 GPU Shield 使用者實測。',
        '用獨立測試證明動態降功率及 per-pin 偵測效果；清楚顯示觸發門檻、原因、保護狀態和事件紀錄，並控制相較競品的成本。',
        '完整留言已讀；產品實測不足',
        'https://www.techpowerup.com/forums/threads/cooler-master-launches-mwe-gold-v4-series-with-gpu-shield.349823/'
    ),
    'OptiGuard': (
        '使用者期待每 pin 電流與溫度監控，但本期未讀到上市後實測優點。',
        '仍標示 coming soon、尚未成為標準配備；使用者擔心重演競品保護失效案例。',
        '縮短上市與普及時程；上市前公布雙端過熱、感測器失效、接觸不良及長時間負載測試，並設計失效安全模式。',
        '期待／進度批評，無實測案例',
        'https://www.techpowerup.com/forums/threads/seasonic-prime-tx-1600w-noctua-edition.349357/post-5758199'
    ),
    'Ampinel': (
        '留言將其視為少數具監控或主動控制能力的裝置。',
        '被評為成效有限；會增加故障點，有約兩次插拔後劣化、安裝空間、缺貨、讀值準確性及均流無法修復高阻抗接點的疑慮。2026-07-30 又出現一件論壇轉述的 Ampinel 熔損案例。',
        '優先調查並公開熔損案例的根因；提高端子與插拔壽命，公布量測精度、均流效果、失效模式和 GPU 適配表，並考慮把技術整合進 PSU 以減少額外接點。',
        '多則討論；含一件未獨立驗證的熔損轉述',
        'https://www.techpowerup.com/forums/threads/close-call-5090-burnt-cable.334508/post-5762386'
    ),
    'ROG Equalizer': (
        '4-spring contact 與 busbar 被認為能增加接觸面；有實際購買者確認可搭配非 ASUS PSU，白色線材也較容易看出變色。',
        '使用者確認它不做主動電流平衡；接點材料、金鍍層與保固條件不透明，且 PSU 端未均流。價格效益被評為可疑，也有燒痕報導真偽造成信任問題。',
        '明確改正或限制「Equalizer／均流」行銷說法；公開跨 PSU 保固、鍍層、材料、接觸電阻與插拔壽命；加入溫度感測／failsafe，並提供兩端 per-pin 測試。',
        '具體設計討論與購買者回報',
        'https://www.techpowerup.com/forums/threads/close-call-5090-burnt-cable.334508/post-5760564'
    ),
    'Titanload': (
        '使用者認為其 pin 內部接觸較強、載流餘裕高於一般接頭。',
        '英文技術資料不足；仍屬被動強化，未監測接觸劣化，也被視為緩解而非永久解法。',
        '提供多語技術資料及獨立的接觸電阻、溫升、插拔壽命和長時間高電流測試；增加溫度／電流警示能力。',
        '正面比較，缺少長期實測',
        'https://www.techpowerup.com/forums/threads/asus-now-bundles-rog-equalizer-cable-with-thor-iii-strix-platinum-psus.349555/post-5731303'
    ),
    'T-Guard': (
        '本期未讀到使用者實測優點。',
        '本期未讀到使用者故障或使用評價，無法判斷實際優缺點。',
        '研究缺口：提供第三方與使用者測試樣品，公開感測位置、門檻、反應時間、保護動作及失效安全測試。',
        '使用者證據不足',
        'https://www.techpowerup.com/forums/threads/gigabytes-new-gaming-psus-secure-top-tier-gpus-with-exclusive-t-guard.348271/'
    ),
    'ThermalProtect': (
        '使用者反覆形容它簡單、便宜、可跨 PSU；有約 400W 長時間負載後 hard shutdown、可能避免再次熔損的個案。',
        '仍非完整保護或根因修正；觸發會直接中斷使用，多產品串接後的感測位置與效果不清楚，且機殼常難保留建議彎折空間。',
        '提供觸發前警告、離線事件記錄及觸發後指引；公布與 WireView／PSU pin monitoring 串接時的感測邊界；改善低高度、90 度與不同機殼相容性。',
        '實際觸發個案與多則購買評價',
        'https://www.techpowerup.com/forums/threads/close-call-5090-burnt-cable.334508/post-5753286'
    ),
    'TempGuard': (
        '留言認為感測器位置接近 PSU 專用端子的潛在熔損處。',
        '有個案回報保護線兩側失效、PSU 端嚴重熔損；Reddit 留言進一步質疑 thermistor 位在錯側或反應太慢，顯示單一溫度路徑可能未阻止事故。',
        'GPU／PSU 兩端獨立感測並交叉驗證；把感測器貼近高電流接點，加入自我檢查、斷線即保護、快速切斷與非揮發事件記錄，公布完整失效模式測試。',
        '單一嚴重失效個案與跨論壇討論',
        'https://www.reddit.com/r/ASRock/comments/1utcp5x/asrock_tempguard_failed_to_shut_down_system_after/'
    ),
}
pm_info_reviewed = {
    'WireView': (
        '多位實際使用者肯定逐 pin 電流、電壓、溫度、警報與記錄；Wired 版可接主機板電源開關執行自動關機。年度資料中至少兩例由異常讀值找到線材／端子問題：一例為退縮 pin，另一例為單 pin 僅約 0.8A，換線後都恢復。另有一個月使用者肯定做工、客服與 HWiNFO 整合。',
        '不是主動均流，且增加一組 12V-2x6 接點。安裝受 GPU 散熱器、側板、接頭方向與支架限制；拆裝亦有損傷 GPU 卡扣的個案。舊版使用者曾忽略告警後發生熔損；軟體效能回報正反並存，不能推論所有系統都受影響。對已有 GPU 內建逐 pin 監控的使用者，功能與成本可能重複。',
        'P0：告警後直接顯示「停止負載、關機、檢查三端、換線或送修」流程，並讓自動關機成為容易完成的標準安裝。P1：提供趨勢、基準與三端故障定位，降低額外接點與機械負載，公布 GPU／機殼／方向適配表。P1：修正軟體輪詢負載與斷線，提供不常駐也能保留事件記錄的方法。P2：針對已有內建監控的 GPU 清楚說明額外價值。',
        '高：年度內有多篇安裝、長期使用、異常定位、告警、關機與售後案例；正反經驗並存',
        'https://www.reddit.com/r/ThermalGrizzly/comments/1v1r6oc/just_got_the_wireview_pro_ii_and_immediately_got/'
    ),
    'GPU Safeguard': (
        '實際使用者重視可自訂單 pin 電流與 pin 差異門檻、異常後降載及 PSU 內建保護。一名使用者回報 7A 測試門檻觸發警報並把 power limit 降至 75%；另一項 7A 測試則觸發整機關機。另有使用者在某 pin 變成 0A 時收到警示並換線。開源 Linux 工具可把兩組 12V-2x6 逐 pin 資料輸出到 JSON／Prometheus。',
        '主要阻力是高價、供貨、只有高瓦數型號、beta Afterburner／MSI 軟體依賴、USB 安全、讀值名稱與預設門檻不透明。Ai1300TS 使用者曾把整機 +12V rail 與 GPU pin 合計誤相比較，顯示介面定義不夠清楚；另有兩台個人樣本回報高負載 coil whine 與一條線從接頭脫落，但也有使用者在更高負載下表示安靜，不能推論為普遍缺陷。',
        'P0：硬體層保留不依賴 Windows 的關機保護，調查線材脫落並公布失效安全行為。P1：在介面清楚區分整機 rail、GPU connector 與逐 pin 數值，公布預設／可調門檻、量測誤差、反應時間、USB 協定與驗證方法。P1：提供正式非 beta 設定介面、Linux 套件、Prometheus exporter 或平台無關 API。P2：改善高負載噪音並下放至較低瓦數／價位。',
        '高：年度內有多篇購買、安裝、設定、telemetry、降載／關機與產品可靠性經驗；門檻與反應仍多為使用者測試',
        'https://www.reddit.com/r/MSI_Gaming/comments/1uxj6a2/msi_mpg_ai1600ts_perpin_current_monitoring_i/'
    ),
    'GPU Shield': (
        '論壇主文說明 PSU 可偵測異常電流、主動保護並以 LED 警示；留言認為把保護整合進主流 750–1000W PSU，可能比另購高價轉接器更容易普及。',
        '年度內沒有讀到 GPU Shield 擁有者的實際觸發或長期使用案例。使用者另詢問可搭配既有 PSU 的獨立版本，但沒有上市答覆；「主動保護」實際採降功率、斷電或其他動作仍缺少完整公開條件。',
        'P0：公開異常條件、反應時間與觸發後的確切動作。P1：以獨立測試展示單 pin 高阻抗、逐步鬆脫、長時間高載與感測器失效情境，並提供可追溯事件記錄。P2：保留 750–1000W 主流價位，評估可供既有 PSU 使用的獨立版本。',
        '低：只有產品發布、購買需求與論壇意見，無使用者觸發實測',
        'https://www.techpowerup.com/forums/threads/cooler-master-launches-mwe-gold-v4-series-with-gpu-shield.349823/'
    ),
    'OptiGuard': (
        '留言期待 PSU 內建逐端電流與溫度保護，並希望既有相容 PSU 可取得升級線材。',
        '2026 年資料只讀到支援型號、coming soon、企業版定位與延期討論，沒有上市後觸發、長期負載或失效案例。等待者已有人改買 MSI；另有使用者不喜歡藍牙依賴、希望 USB 或平台無關介面。',
        'P0：上市前公布雙端過熱、單 pin 高阻抗、感測器斷線及控制器失效時的保護測試。P1：公布消費版明確時程、支援型號、既有客戶升級方式、門檻與事件記錄。P2：提供 USB／本地 API，避免只限最高價或企業平台。',
        '低：全年仍未讀到上市後使用者實測；主要是延期與功能期待',
        'https://www.techpowerup.com/forums/threads/seasonic-prime-tx-1600w-noctua-edition.349357/post-5758199'
    ),
    'Ampinel': (
        '部分使用者看重主動均流與 AquaSuite。年度內一名實際擁有者回報約 400W 時各 pin 約 5–6A、PSU 端溫度由約 50–58°C 降至 40–45°C，並肯定監控與控制；這是單一系統、無對照測試，不能推論普遍幅度。',
        '實際疑慮包括約 100 歐元價格、長期預購、約 50 mm 空間、凹入式／FE GPU 相容性、軟體更新訂閱與額外接點。一名頻繁拆裝者回報約兩次插拔後接點劣化；另有熔損轉述但缺原始測試，不能據此估算失效率。',
        'P0：調查並公開接點劣化與熔損轉述的根因、保護是否觸發及失效安全行為。P1：公布均流前後數據、量測精度、插拔壽命、GPU 適配與高阻抗接點測試。P1：評估把均流與監控整合進 PSU，減少中間接點。',
        '中：有單一正面擁有者數據與拆裝負面經驗；熔損仍為未獨立驗證的轉述',
        'https://www.techpowerup.com/forums/threads/close-call-5090-burnt-cable.334508/post-5762386'
    ),
    'ROG Equalizer': (
        '實際擁有者回報可搭配非 ASUS、具有原生 12V-2x6 的 PSU；部分留言看重 4-spring 接點、busbar、較高載流餘裕與白色線材較容易看出變色。也有使用者表示目前沒有異常。',
        '論壇意見高度分歧：有人認為它比標準線材有更高容錯，也有人質疑名稱造成「主動均流」誤解、PSU 端沒有對稱 busbar、金／錫異材接觸、長期 17A 說法及價格效益。網路燒痕圖片缺乏完整背景，多名留言者質疑真實性，因此不能列為已證實失敗案例。',
        'P0：明確說明它是被動式載流強化，不宣稱可主動控制每路電流。P1：公開 GPU／PSU 兩端逐 pin 測試、接觸材料、鍍層、接觸電阻、插拔壽命與長期高載結果。P2：說明非 ASUS PSU 的功能與保固差異，以及 GPU-First 額外功能的限制。',
        '中：有擁有者經驗與技術討論，但長期實測少、網路失敗圖片未證實',
        'https://www.reddit.com/r/ASUSROG/comments/1uktwty/ive_seen_reports_of_the_asus_rog_equalizer_cable/'
    ),
    'Titanload': (
        '一名實際買家肯定 Titanload 的做工與端子質感，並把較高載流餘裕視為價值；其他留言也把它視為 Equalizer 的替代方向。',
        '買家發文當下尚未提供長時間負載或故障注入結果；英文技術資料、全球供貨與 PSU／GPU 相容性資訊仍不足。做工評價不能視為保護效果驗證。',
        'P1：提供可核對的多語規格、端子結構、接觸電阻、溫升、插拔壽命與長時間高電流測試。P2：改善全球供貨與 GPU／PSU 相容性資訊。',
        '低：有單一買家做工評價，但尚無長期或保護觸發測試',
        'https://www.techpowerup.com/forums/threads/asus-now-bundles-rog-equalizer-cable-with-thor-iii-strix-platinum-psus.349555/post-5731303'
    ),
    'T-Guard': (
        '2026 年讀到產品機制發布，但未讀到可核對的擁有者優點或實際觸發案例。',
        '沒有使用者故障、長期使用或保護動作資料，因此不能判斷實際優缺點。',
        '研究缺口：提供第三方測試樣品，公開感測位置、門檻、反應時間、保護動作及感測器／控制器失效時的安全行為。',
        '使用者證據不足：有產品機制明細，無擁有者實測',
        'https://www.techpowerup.com/forums/threads/gigabytes-new-gaming-psus-secure-top-tier-gpus-with-exclusive-t-guard.348271/'
    ),
    'ThermalProtect': (
        '多則留言把它評為簡單、約 25 美元、可搭配具有原生 12V-2x6 端口的不同 PSU。TechPowerUp 有一名使用者回報約 400W、兩小時負載後硬關機，認為可能避免第二次熔損；這是單一觸發案例。另有實際買家肯定線材做工與易用性。',
        '它依溫度開關切斷 sense pin，不監控逐 pin 電流，也不能修復接點根因；觸發時會直接中斷工作。WireView 與 ThermalProtect 串接是否改變感測效果，留言出現相反看法，缺乏正式相容性測試。感測位置距接頭仍是使用者疑問。',
        'P0：公布與 WireView／其他監控器串接時的保護邊界及測試結果。P1：加入觸發前警告、觸發原因與事件記錄，並提供觸發後檢查／換線指引。P2：提供更低高度、90 度與不同機殼版本，同時維持簡單低價。',
        '中高：有購買評價與一件實際硬關機案例；串接效果未驗證',
        'https://www.techpowerup.com/forums/threads/close-call-5090-burnt-cable.334508/post-5753286'
    ),
    'TempGuard': (
        '本期沒有讀到成功觸發的擁有者案例。',
        '兩篇 Reddit 貼文與 TechPowerUp 留言都指向同一件外部報導：PSU 端嚴重熔損後系統仍未關機。這是一件事件，不代表普遍失效率。留言者推測 thermistor 位置、PSU 回授迴路或製造缺陷可能是原因，但本期沒有原廠根因報告，不能把任何推測寫成已證實。',
        'P0：公布該事件的根因、感測器是否正常、實際溫度與未關機原因。P0：GPU／PSU 兩端獨立感測，感測器斷線或讀值異常時採失效安全。P1：提供快速切斷、非揮發事件記錄及雙端高阻抗／局部熱點測試。',
        '低至中：一件跨論壇轉載的嚴重案例；故障原因尚未證實',
        'https://www.reddit.com/r/ASRock/comments/1utcp5x/asrock_tempguard_failed_to_shut_down_system_after/'
    ),
}
pm_info.update(pm_info_reviewed)
pm_info['GPU Tweak III Auto-Shutdown'] = (
    '目前有 TechPowerUp 與 Reddit 兩篇討論可讀。Dr. Dro（TechPowerUp）認為軟體在偵測到持續性高電流時主動介入關機，即使未必完美，仍優於單純警告；Reddit 討論（r/nvidia）中也有留言建議可額外監控 12VHPWR 電壓驟降作為輔助判斷訊號，補強單純電流監控的盲點。',
    'kazuviking（TechPowerUp）以 ThermalProtect、Seasonic OptiGuard 等類似設計為例，質疑感測位置若沒有直接貼在接頭本體，即使線材已達 95°C 也可能不觸發。Reddit 討論中多則留言強調功能需要「正確的 PSU＋GPU 組合」，並非任何 ASUS 顯示卡都適用，僅限少數搭載 Power Detector+ 的 ROG Astral／ROG Matrix 高階卡；另有留言批評「連接器不是全貌」——認為 Nvidia 公版設計拿掉了逐 pin 監控與熱關機機制，各板卡廠只能各自加裝專屬方案彌補，形成各家補丁不一的局面。功能預設關閉、需使用者手動啟用。',
    'P1：公開 12.5A 門檻與可調觸發秒數（1～5 分鐘）的訂定依據，並說明是否會隨韌體或硬體世代調整。P1：提供不需額外設定即可啟用的建議預設值，並清楚說明關機後如何判斷是誤報還是真正過流。P1：考慮納入電壓驟降等輔助監控訊號，補強單純電流門檻的偵測盲點。P2：擴大支援到更多具備逐 pin 監控硬體的機型，而非僅限最高階卡。',
    '剛列入追蹤：TechPowerUp／Reddit 各 1 篇討論，尚無擁有者觸發或長期使用回報',
    'https://www.techpowerup.com/forums/threads/asus-gpu-tweak-iii-adds-auto-shutdown-to-prevent-12v-2%C3%976-meltdowns.351662/'
)
pm_info['EZDIY-FAB Alpha TS13'] = (
    'TechPowerUp 由 W1zzard 親自評測：官方描述可在不需軟體的情況下即時顯示 GPU 功耗與接頭溫度，評測並以 600W 負載＋熱風槍測試驗證 85°C 警報確實會觸發。',
    '留言者 Erratic4^2 表示雖然肯定這個裝置的構想，但如果要花大錢組頂級主機，他仍寧願多花錢買有逐 pin 監控的 WireView Pro II（並表示自己已經買了）。另一位留言者 roman 質疑評測本身的量測方法：分流電阻＋類比數位轉換器的做法準確度未經已知誤差的量測儀器驗證，建議應改用 TRUE RMS 電流鉗表或搭配示波器的電流探棒才能驗證讀值。這款產品本身只顯示整體功耗與單點接頭溫度，不像 WireView／Ampinel 有逐 pin 電流資料，也沒有自動關機或降載機制。',
    'P1：公開量測方法與校正依據，說明功耗與溫度讀值的誤差範圍。P1：考慮加入逐 pin（而非僅整體）電流顯示，或至少說明為何選擇單點溫度感測而非逐 pin。P2：累積更多獨立使用者的長期使用與觸發案例，目前僅有 1 篇官方評測、尚無社群長期回報。',
    '剛列入追蹤：僅 1 篇 TechPowerUp 官方評測與討論串，尚無使用者長期回報',
    'https://www.techpowerup.com/review/ezdiy-fab-alpha-ts13/'
)
pm_info['VGA 12+4PIN OCP Dongle'] = (
    '官方規格提供六路 +12V 電流監控、兩級 ARGB／蜂鳴器警示，以及單路超過 12A 持續 10 秒後的黑畫面保護流程；定價 1,190 元，低於多數帶螢幕的逐 pin 監控器。Reddit 留言者認為它可作為多張高功耗顯示卡的較低成本保護選項。',
    '本期沒有獨立故障注入或長期使用測試。TechPowerUp 留言集中質疑超過 12A 後仍等待 180 秒才進入 15 秒倒數、黑畫面不易與驅動程式當機區分、轉接線增加兩個接頭，以及首波僅隨 Leadex VIII 電源組合販售。模組化電源線腳位不共通，Reddit 也出現相容性資訊互相矛盾的情況。',
    'P0：說明黑畫面保護的實際電路動作、是否會中止 GPU 取電，以及裝置自身失效時的安全行為。P0：縮短或允許設定高電流等待時間，但保留不可超過的安全上限。P1：加入非揮發事件記錄，並公布相容 PSU／線材、獨立販售、保固與顯示卡損害處理條件。P1：以高阻抗接點、單路過流與電流失衡做可重現測試，並評估加入接頭溫度感測。',
    '低至中：官方機制已確認；有兩串完整功能與疑慮討論，但尚無擁有者觸發或長期測試',
    'https://www.super-flower.com.tw/tw/products-detail/OCPD_M/'
)

# Refresh product-level evidence and priorities with the newly read owner posts.
pm_info.update({
    'GPU Safeguard': (
        pm_info['GPU Safeguard'][0] + ' 本週新增一名擁有者表示使用體驗良好，並特別肯定 Afterburner 整合；該留言未提供觸發數據。',
        pm_info['GPU Safeguard'][1],
        pm_info['GPU Safeguard'][2],
        '高：已有多篇設定、telemetry、降載／關機與產品可靠性經驗；本週新增單一正面整合評價，但沒有新增觸發測試',
        'https://www.reddit.com/r/Corsair/comments/1v1xadu/corsair_thermal_protect_cable_vs_rog_gpu_power/'
    ),
    'Ampinel': (
        '實際擁有者肯定 AquaSuite／裝置軟體易用；既有單一系統曾回報約 400W 時各 pin 約 5–6A。新讀到的水冷安裝案例在換貨後，重載時各 pin 維持綠燈且不再不穩，但這些都不是受控對照測試。',
        '除價格、供貨、額外接點與約 50 mm 空間外，新案例顯示剛性外殼可能干涉水冷背板／記憶體水冷配置，甚至需切削背板或機殼。發文者第一顆有 pin 後縮、接頭晃動並造成不穩，另一名買家也回報晃動與偶發黃色 pin；樣本很少，不能推算普遍故障率。',
        'P0：調查後縮 pin、接頭晃動與不穩案例，建立出貨端子高度／保持力檢驗及快速換貨標準。P1：公開插拔壽命、保持力、端子公差、GPU／水冷背板／機殼空間適配表與實寸模板。P1：在說明中精確區分「平衡電壓降」與負載／電流平衡，並公開受控前後測試。',
        '中高：新增多名實際安裝者的軟體、換貨、端子與空間經驗；仍缺大樣本與受控保護測試',
        'https://www.reddit.com/r/watercooling/comments/1v5wh2i/ampinel_installed/'
    ),
    'ROG Equalizer': (
        '擁有者回報可搭配非 ASUS 原生 12V-2x6 PSU。本週一項 RTX 5090 快速比較中，Equalizer 在最高約 600W 時各 pin 未超過 9A，原線則有 pin 超過 9.2A 並觸發軟體警報；另有部分 5080／5090 使用者表示目前運作正常。這些都是單一系統觀察。',
        '測試品質不一致：一篇主文聲稱同為「100%」，但留言依逐 pin 值反算出兩組總功率明顯不同，不能當成同負載證據。另一名 RTX 5080 使用者換 PSU／Equalizer 後差距由約 0.4A 變成約 2A，尚無根因。留言亦擔心橋接後 GPU 讀值與橋接前 PSU 讀值各只覆蓋部分路徑；長期數據、門檻解釋與保固仍不足。',
        'P0：在軟體直接說明逐 pin 警報門檻、總功率、最大差值、持續時間及「何時重插／換線／停機」，避免只顯示單一紅黃值。P1：發布固定總功率、同卡同 PSU、重複多次的 GPU／PSU 雙端逐 pin 測試，說明 busbar 前後各感測到什麼。P1：公開端子材料、接觸電阻、插拔壽命與不同 PSU 的保固／相容性。',
        '中高：新增三篇含數值的擁有者貼文，但一篇測試控制遭留言質疑、另一篇尚無診斷結果，長期證據仍少',
        'https://www.reddit.com/r/ASUSROG/comments/1velpgc/rog_equalizer_vs_serie_thor_3/'
    ),
    'ThermalProtect': (
        '既有資料含多則低價、易用評價與一件約 400W、兩小時後硬關機的單一觸發案例。本週新增的比較詢問顯示使用者特別需要長期可靠性、預警、誤報與 Equalizer 對照，但可見留言沒有同時長期使用兩者的直接證據。',
        '它依溫度開關切斷 sense pin，不監控逐 pin 電流，也不能修復接點根因；觸發時會中斷工作。外部測試曾因未依產品動作方式執行而重測，論壇留言沒有提供足以獨立確認結果的原始數據；與其他監控器串接、感測位置及長期誤報率仍不清楚。',
        'P0：公布可重現的故障注入方法、觸發溫度／時間、誤報條件與外部重測完整數據。P1：提供觸發前警告、非揮發事件記錄、觸發後檢查／換線指引，以及與 WireView／PSU 監控串接的邊界。P2：建立長期使用與誤報統計，並維持低價、低高度與多機殼版本。',
        '中高：已有一件實際硬關機案例與購買評價；本週新增明確比較需求，但沒有新的 ThermalProtect 長期或觸發實測',
        'https://www.reddit.com/r/Corsair/comments/1v1xadu/corsair_thermal_protect_cable_vs_rog_gpu_power/'
    ),
})

pm_info.update({
    'GPU Safeguard': (
        pm_info['GPU Safeguard'][0] + ' NGA玩家社區 使用者另描述過流時先鳴叫、未處理可能強制斷電；另一串提到依電流差異可能延遲約 3 分鐘或立即關機。這些是論壇描述，沒有相同條件的重現測試。',
        pm_info['GPU Safeguard'][1] + ' NGA玩家社區 留言擔心保護失效仍可能燒損、保固爭議、插拔壽命與延遲關機；Ai1300TS 討論也出現價格、16A 插頭與 110V 相容性疑慮。',
        pm_info['GPU Safeguard'][2] + ' P0：清楚區分鳴叫、降載、延遲關機與立即斷電的觸發條件，並公開 3 分鐘延遲是否可設定；P1：針對保護失效、接頭插拔壽命與保固處理提供可核對流程。',
        '高：新增兩篇 NGA玩家社區 功能與使用疑慮討論；仍缺相同條件的獨立重現測試',
        'https://bbs.nga.cn/read.php?tid=45950741'
    ),
    'ROG Equalizer': (
        pm_info['ROG Equalizer'][0] + ' Chiphell 使用者確認線材很硬、金屬環會延長 GPU 端並限制彎折；部分使用者認為直立顯卡較容易安裝。',
        pm_info['ROG Equalizer'][1] + ' NGA玩家社區 有燒損回報但未提供電源型號；留言另質疑端子鍍層、線材應力與接口品質。NGA玩家社區／Chiphell 多串也批評 399 元價格，且沒有足夠長期測試。',
        pm_info['ROG Equalizer'][2] + ' P1：公開金屬環所需側板／彎折空間與安裝方向，並提供不同機殼實寸；P1：針對燒損回報公布電源、負載、插接狀態與兩端量測，避免以單一案例或圖片下結論。',
        '中高：新增 NGA玩家社區 與 Chiphell 的價格、安裝、燒損疑慮；仍缺可比的長期安全測試',
        'https://www.chiphell.com/thread-2847439-1-1.html'
    ),
    'ThermalProtect': (
        pm_info['ThermalProtect'][0] + ' Chiphell 主文具體描述 GPU 端熱敏元件與超溫後斷開 sense 的機制，並記載約 30mm 的模組位置。',
        pm_info['ThermalProtect'][1] + ' Chiphell 留言仍質疑接頭標準根因、感測熱點代表性與機制能否真正避免熔損；新增資料沒有使用者觸發結果。',
        pm_info['ThermalProtect'][2] + ' P1：公開感測器與實際熱點的校準、觸發門檻、反應時間與誤報測試，並以完整高阻抗／局部加熱情境驗證。',
        '中高：新增兩篇 Chiphell 機制說明；仍無新增使用者觸發測試',
        'https://www.chiphell.com/thread-2849232-1-1.html'
    ),
    'OptiGuard': (
        pm_info['OptiGuard'][0] + ' NGA玩家社區 留言僅提到 SeaSonic OptiGuard 曾存在或尚未普及，沒有擁有者的功能驗證。',
        pm_info['OptiGuard'][1] + ' 新增資料仍未提供上市後觸發、長期負載或失效案例，不能把產品機制說明當成實際效果。',
        pm_info['OptiGuard'][2] + ' P1：以可核對的上市型號、電流／溫度記錄與失效安全測試，補足「已提到但未實測」的證據缺口。',
        '低：NGA玩家社區 只有留言提及，沒有 OptiGuard 擁有者實測',
        'https://bbs.nga.cn/read.php?tid=46586390'
    ),
})

pm_info.update({
    'GPU Safeguard': (
        pm_info['GPU Safeguard'][0] + ' 百度貼吧新增一件 MSI RTX 5090 轉接線端子熔化案例，以及一件顯卡供電針腳發黑但尚未熔化的早期異常案例；兩篇都沒有提到 GPU Safeguard+，因此只能作為 MSI 顯卡／售後情境，不能當成 Safeguard+ 的失效證據。',
        pm_info['GPU Safeguard'][1] + ' 百度案例顯示使用者在正常使用後拆機才發現 12V 端子發黑與塑膠熔化；可見留言主要建議改用原生 12V-2x6，沒有完整溫度、電流或售後處理結果。',
        pm_info['GPU Safeguard'][2] + ' P1：提供 MSI 顯卡燒損後的檢查、停用、送修與替換線材流程；P1：讓 Safeguard+ 與 MSI 顯卡／電源售後系統能記錄並追蹤端子早期異常，避免使用者只能在拆機後才發現熔損。',
        '高：新增百度兩件 MSI／顯卡端子異常案例，但未直接驗證 Safeguard+ 效果',
        'https://tieba.baidu.com/p/10924984358'
    ),
    'ROG Equalizer': (
        pm_info['ROG Equalizer'][0] + ' 百度貼吧補充中國市場搭載 Equalizer 的 ROG STRIX 電源上市資訊與線材規格說明；這是產品介紹，不是使用者實測。',
        pm_info['ROG Equalizer'][1] + ' 百度新增內容沒有擁有者的溫升、電流分配或長期使用結果，不能把貼文宣稱的 17A、600W 或溫度數字當作獨立驗證。',
        pm_info['ROG Equalizer'][2] + ' P1：針對中國上市型號公開可重現的 GPU／PSU 兩端實測、測試條件與長期數據；把宣傳規格與使用者可驗證結果分開呈現。',
        '中高：新增中國市場產品資料；沒有新增使用者實測',
        'https://tieba.baidu.com/p/10636501041'
    ),
})

pm_info['PinProtect／PinProtect+'] = (
    '使用者重視把逐 pin 電流監控與保護整合在 PSU 內，不必加裝外接轉接器；PinProtect 固定常駐，PinProtect+ 另有 iCUE 六路即時讀值、通知、事件記錄與可調門檻／延遲。',
    '目前沒有讀到擁有者實際觸發或長期使用資料。論壇具體疑慮包括第二代 RM1200e 與舊代同名、料號／供貨／價格難辨識，警示 LED 在封閉機殼內不易看見，自動切斷可能造成工作中斷，以及 PSU 端電流監控不能直接量到 GPU 接頭局部溫度。',
    'P0：清楚標示支援型號、世代與料號，並公布逐 pin 門檻、量測精度、反應時間及故障注入測試。P1：在切斷前提供明確蜂鳴警示、可匯出事件記錄與安全上限內的處置時間設定。P1：說明 iCUE 未執行時的硬體獨立保護、溫度監控邊界及保固流程。',
    '中：官方機制清楚，已讀多個論壇完整討論；尚無擁有者觸發或長期驗證',
    'https://www.reddit.com/r/Corsair/comments/1xdndw4/new_rme_psu_with_12v2x6_perpin_overcurrent/'
)

multi_keyword_map = {
    'https://bbs.nga.cn/read.php?tid=47361387':
        ['GPU Shield', 'GPU Safeguard'],
    'https://bbs.nga.cn/read.php?tid=47343776':
        ['GPU Shield', 'GPU Safeguard', 'ROG Equalizer'],
    'https://www.reddit.com/r/LinusTechTips/comments/1vqt4vi/regarding_melting_12vhpwr_power_cables_for_nvidia/':
        ['ROG Equalizer', 'WireView', 'Ampinel', 'GPU Safeguard', 'ThermalProtect', 'PinProtect／PinProtect+'],
    'https://www.hardwareluxx.de/community/threads/thermalprotect-pinprotect-und-pinprotect-corsair-zeigt-schutzl%C3%B6sungen-f%C3%BCr-12v-2x6-problematik.1379683/':
        ['ThermalProtect', 'PinProtect／PinProtect+'],
    'https://www.chiphell.com/thread-2849232-1-1.html':
        ['ThermalProtect', 'PinProtect／PinProtect+'],
    'https://www.reddit.com/r/watercooling/comments/1vo2wsd/is_this_something_ideal_to_look_on_brand_new/':
        ['Ampinel', 'WireView', 'ThermalProtect'],
    'https://www.chiphell.com/thread-2862733-1-1.html':
        ['Titanload', 'ROG Equalizer'],
    'https://www.reddit.com/r/MSI_Gaming/comments/1ur8ybe/avoid_msi_ai1600ts_if_you_when_something_silent/':
        ['GPU Safeguard', 'OptiGuard'],
    'https://www.reddit.com/r/buildapc/comments/1uoypxa/need_some_advise_on_the_new_msi_mpg_ai1300_ts/':
        ['GPU Safeguard', 'WireView'],
    'https://www.reddit.com/r/nvidia/comments/1uy88v8/rtx_pro_6000_blackwellmaxq_vs_5090_for_multiagent/':
        ['WireView', 'GPU Safeguard', 'Ampinel'],
    'https://www.reddit.com/r/pcmasterrace/comments/1uxhwl3/wireview_melted_on_my_5090/':
        ['WireView', 'ThermalProtect', 'TempGuard', 'ROG Equalizer'],
    'https://www.reddit.com/r/ASRock/comments/1utcp5x/asrock_tempguard_failed_to_shut_down_system_after/':
        ['TempGuard', 'ThermalProtect', 'GPU Safeguard'],
    'https://www.reddit.com/r/pcmasterrace/comments/1utff9u/my_asrock_tempguard_cable_failed_and_melted_on/':
        ['TempGuard', 'GPU Safeguard'],
    'https://www.reddit.com/r/pcmasterrace/comments/1uszwr7/its_just_comical_at_this_point/':
        ['TempGuard', 'GPU Safeguard', 'WireView', 'ThermalProtect'],
    'https://www.reddit.com/r/nvidia/comments/1ust8i0/avoid_12vhpwr_connectors_melting_on_5090/':
        ['Ampinel', 'WireView', 'ROG Equalizer', 'GPU Safeguard'],
    'https://www.reddit.com/r/nvidia/comments/1uoepk0/installed_wire_view_2_and_corsair_thermal_protect/':
        ['ThermalProtect', 'WireView', 'GPU Safeguard', 'OptiGuard', 'Ampinel', 'ROG Equalizer'],
    'https://www.reddit.com/r/overclocking/comments/1umu2yx/questions_about_12v2x6_connector_wear_and_cable/':
        ['Ampinel', 'ROG Equalizer', 'GPU Safeguard'],
    'https://www.reddit.com/r/pcmasterrace/comments/1unjyw4/it_really_can_happen_to_you_too/':
        ['WireView', 'Ampinel', 'GPU Safeguard', 'ThermalProtect'],
    'https://www.reddit.com/r/ASUSROG/comments/1uktwty/ive_seen_reports_of_the_asus_rog_equalizer_cable/':
        ['ROG Equalizer', 'WireView', 'ThermalProtect'],
}
content_review_overrides = {
    'https://www.reddit.com/r/ThermalGrizzly/comments/1v1r6oc/just_got_the_wireview_pro_ii_and_immediately_got/': {
        'summary': '使用者安裝 WireView Pro II 後，Line 5／6 幾乎沒有電流；約 450W 遊戲負載隨即觸發 imbalance 告警。照片中後來被留言者指出有兩個退縮 pin，使用者最後更換 PSU 線材，問題解決。',
        'comments': '留言依序建議重新插妥 GPU、WireView 與 PSU 端、檢查 pin 位置並更換線材。這是一個告警協助找到線材／端子問題的成功個案；沒有證據顯示 WireView 修復了問題，實際修復動作是換線。',
    },
    'https://www.reddit.com/r/ThermalGrizzly/comments/1v0uzle/wire_view_2_software_causes_huge_performance/': {
        'summary': '發文者使用 WireView 軟體 1.0.7 常駐系統列時，VR 模擬賽車由穩定 90 FPS 降至部分場景低於 60 FPS；關閉後恢復。另一名 5090 使用者也表示關閉軟體後，功耗與跑分恢復。',
        'comments': '官方人員回覆軟體主要用於設定與韌體更新，裝置可獨立運作，不必常駐。其他使用者經驗分歧：有人沒有差異，也有人把取樣間隔由 500ms 改成 3000ms 後改善。可確認「部分系統存在效能問題」，不能寫成所有使用者固定損失 30%。',
    },
    'https://www.reddit.com/r/ThermalGrizzly/comments/1uy826k/wireview_pro_ii_wired_on_rtx_pro_6000_finally_the/': {
        'summary': 'RTX Pro 6000 使用者完成 Wired 版安裝、Y-cable 自動關機測試及兩支溫度探頭配置，並表示因此願意讓超過 600W 的 AI inference 工作無人運行；這是使用者信心與測試結果，不代表客觀「完全安全」。',
        'comments': '留言肯定監控與關機，也指出裝置不做 Ampinel 式均流、會增加一組 12V-2x6 接點，且兩個 pin 接近 9A 時仍有人主張應限功率。Ampinel 缺貨、GPU 相容性及 WireView 有現貨，使部分人把 Wired 版視為可取得的折衷方案。',
    },
    'https://www.reddit.com/r/ThermalGrizzly/comments/1uxhwl3/wireview_pro_melted_on_my_gigabyte_aorus_rtx_5090/': {
        'summary': '舊版 WireView Pro 在平台更換後多次於滿載告警；使用者改以 85–90% power limit 繼續使用，最終在遊戲中再次告警並發現 WireView 與 GPU 端部分熔化。發文者承認先前應更早停止使用並聯絡支援。',
        'comments': '多數留言認為連續告警就是需停止負載、檢查或換線的訊號；也有人指出舊版只會告警、不會自動關機。Thermal Grizzly 要求聯絡客服，後續同意更換接頭並把裝置升級為 Pro II。此案例證明告警本身不足以避免損壞，仍需要明確處置或自動關機。',
    },
    'https://www.reddit.com/r/ASRock/comments/1utcp5x/asrock_tempguard_failed_to_shut_down_system_after/': {
        'summary': '主文是轉貼外部報導：一部使用 ASRock PG1000-PSF 與 RTX 5090 的系統在接頭熔損後仍持續運作，TempGuard 未關機。本頁不是原始擁有者完整測試紀錄。',
        'comments': '一名留言者推測 thermistor 位於不利的接頭側；其他人建議 ThermalProtect 或 MSI Safeguard+。本期未讀到 ASRock 根因報告，因此感測器位置、回授迴路或 PSU 缺陷都只能列為留言推測。',
    },
    'https://www.reddit.com/r/pcmasterrace/comments/1utff9u/asrock_tempguard_failed_to_shut_down_system_after/': {
        'summary': '本頁同樣轉貼 TempGuard 未關機的外部報導，與 r/ASRock 貼文不是兩件獨立事故；應視為同一事件的跨社群討論。',
        'comments': '留言多數批評接頭根因與補救方案。一名 Ai1600TS 使用者描述自己的 Safeguard+ 設定為 9.0A／1.0A，越界約 3 秒後載入 Afterburner 降載 profile；這是個人配置，不能當成所有 MSI PSU 的預設或獨立測試結果。',
    },
    'https://www.reddit.com/r/MSI_Gaming/comments/1upfvw4/msi_psu_safeguard_custom_amp_limits_guide/': {
        'summary': '使用者只列出 Ai1600TS／Ai1300TS 的兩個設定欄位：currentmax 代表單 pin 最大電流，currentdif 代表 pin 間允許差異。',
        'comments': '讀取時顯示 0 則留言，沒有門檻建議、觸發結果或其他使用者驗證；此筆只能證明設定欄位需求，不能支持保護成效結論。',
    },
    'https://www.reddit.com/r/nvidia/comments/1uoepk0/installed_wire_view_pro_ii_and_corsair_thermal/': {
        'summary': 'RTX 5090 使用者同時安裝 WireView Pro II 與 Corsair ThermalProtect，主文只表示降低焦慮，沒有呈現保護觸發或故障測試。',
        'comments': '留言對串接效果沒有共識：有人認為 WireView 改變 sense pin 路徑後會影響 ThermalProtect，也有人依感測位置主張仍可運作。另有使用者把 WireView 與更換整台 Safeguard+ PSU 的成本、機殼空間及保固做比較。報告不判定兩者串接一定有效。',
    },
    'https://www.reddit.com/r/ASUSROG/comments/1uktwty/ive_seen_reports_of_the_asus_rog_equalizer_cable/': {
        'summary': '發文者因一張缺乏背景的 ROG Equalizer 燒痕圖片考慮取消訂單，並詢問長期使用者是否遇過過熱或熔損。',
        'comments': '多名留言者指出圖片只有單一來源、沒有負載與後續資料，甚至懷疑為假圖；另有實際擁有者表示尚未出問題，也有人回報線材姿態會影響逐 pin 電流。可確認使用者信任受未驗證圖片影響，但不能把圖片列為已證實失敗。',
    },
    'https://www.techpowerup.com/forums/threads/close-call-5090-burnt-cable.334508/post-5762386': {
        'summary': '留言者彙整外部社群事故，其中一件被描述為 Ampinel 熔損、GPU 據稱存活；本頁沒有原始擁有者的安裝、負載、告警或回覆紀錄。',
        'comments': '這只能作為待查風險訊號，不能證明 Ampinel 的故障原因或失效率。改善方向應是要求原廠調查接點、安裝狀態、保護是否觸發與 GPU 適配，而不是直接判定產品普遍失效。',
    },
    'https://forums.tomshardware.com/threads/cooler-master-shows-off-new-mwe-gold-v4-power-supplies-and-gpu-shield-adapter-%E2%80%94-per-pin-monitoring-can-dynamically-scale-down-power-to-stop-cables.3896668/': {
        'summary': '主文為 GPU Shield 發表內容，描述逐 pin 監控與動態降功率；本討論串沒有使用者實際觸發或長期測試。',
        'comments': '四則留言主要批評業界以附加產品補救接頭規格，也討論廠商是否能從新保護市場獲利。這些留言反映市場觀感，不構成 GPU Shield 保護效果的驗證。',
    },
    'https://forums.tomshardware.com/threads/cooler-master-mwe-gold-750-v4-power-supply-review-verified-gold-efficiency-with-mainstream-pricing.3897955/': {
        'summary': '主文只有評測導言，列出 750W、Gold 效率、原生 12V-2x6、GPU Shield 監控與 140mm 機身。',
        'comments': '本頁沒有使用者留言，也沒有可讀到的 GPU Shield 觸發測試細節；不能據此整理實際優缺點。',
    },
}

# 2026-09-02 weekly refresh：涵蓋前版（2026-08-26 產生）之後、TechPowerUp／Tom's Hardware
# 已核讀到的新內容。Reddit 本次因匿名搜尋介面失效（未登入時 old.reddit.com 要求登入、
# www.reddit.com 的 search 網址在無登入狀態下會退回不相關的 r/all 最新內容，並非真正的
# 關鍵字搜尋結果）而無法核讀，故本版未涵蓋 Reddit 新增內容；ComputerBase、Hardwareluxx、
# NGA玩家社區、Chiphell、百度貼吧、Overclockers UK、PCGH Extreme 本次亦未查核。
rows.extend([
    {
        'date': '2026-08-18', 'source': 'TechPowerUp Forums', 'keyword': 'GPU Tweak III Auto-Shutdown',
        'keywords': ['GPU Tweak III Auto-Shutdown', 'ROG Equalizer', 'ThermalProtect', 'OptiGuard'],
        'match': '標題＋內文＋留言',
        'title': 'ASUS GPU Tweak III Adds Auto-Shutdown to Prevent 12V-2×6 Meltdowns',
        'summary': '主文說明 ASUS GPU Tweak III V2.1.8.0 為搭載 Power Detector+ 的機型（ROG Astral RTX 5090／5090 LC／5080、ROG Matrix RTX 4090）新增 auto-shutdown：偵測到「持續性高電流」時關機；ASUS 未公開觸發電流門檻與需持續多久。主文並說明此功能建立在既有 ROG Equalizer 線材（被動均流、內部溫度控制在 73°C 以下）與 Power Detector+（先前僅發出警告）之上。',
        'comments': '留言正反並陳：Dr. Dro 認為雖不完美，但已能在失控前介入關機，優於單純警告，同時也承認 ROG Equalizer 本身仍有其問題、沒有完美解法；他另建議與其依賴軟體，不如直接加裝約 25 美元的 Corsair ThermalProtect 線材，可跨品牌、跨世代適用。Darmok N Jalad 質疑「只能用原廠線」的建議會削弱使用者對這類技術的信任。kazuviking 則以 ThermalProtect 與 Seasonic OptiGuard 為例，批評若溫度探頭沒有貼在接頭本體上，即使線材已達 95°C 也可能不觸發，直指這類保護「實際上沒什麼用」；這是留言者個人評價，沒有本串內的獨立測試佐證。',
        'url': 'https://www.techpowerup.com/forums/threads/asus-gpu-tweak-iii-adds-auto-shutdown-to-prevent-12v-2%C3%976-meltdowns.351662/'
    },
    {
        'date': '2026-08-25', 'source': 'TechPowerUp Forums', 'keyword': 'WireView',
        'keywords': ['WireView', 'ROG Equalizer', 'ThermalProtect'],
        'match': '留言',
        'title': "Moore's Law Is Dead - \"A Call To Action\" Over NVidia 5000 Series' Hardware Flaw",
        'summary': '討論串主題聚焦 Nvidia 5000 系列硬體爭議；串中 Sol_Badguy 把「避免 5090 燒毀」的常見作法歸納為一組「longevity maxxers」清單：避免線材尖銳彎折、降壓、高風量機殼散熱、房間空調，並列出 Corsair ThermalProtect、ROG Equalizer、WireView 作為例子。',
        'comments': '新加入會員 Sudo_Apt 附和並自述使用 1200W Leadex VIII、WireView Pro 搭配明顯降壓，於 4K/120Hz、69% 功耗上限下運作正常。該帳號僅有這一則貼文，屬單一自述，沒有告警或觸發細節可供查核，不能推論為普遍安全門檻。',
        'url': 'https://www.techpowerup.com/forums/threads/moores-law-is-dead-a-call-to-action-over-nvidia-5000-series-hardware-flaw.351836/post-5775343'
    },
    {
        'date': '2026-08-30', 'source': 'TechPowerUp Forums', 'keyword': 'ThermalProtect',
        'keywords': ['ThermalProtect', 'ROG Equalizer'], 'match': '留言',
        'title': 'critique my pc part picker',
        'summary': '留言者在幫忙檢視一套 1200W／i9／RTX 5090 组裝清單時，建議把 Corsair ThermalProtect 或 ROG Equalizer 線材一併編入預算，並確認與該組裝使用的 be quiet! Dark Power 系列相容。',
        'comments': '本頁沒有進一步的觸發或長期使用細節，屬建議選購清單中的常見搭配推薦，性質與既有「Power Supply for my build」條目類似。',
        'url': 'https://www.techpowerup.com/forums/threads/critique-my-pc-part-picker.352125/post-5779344'
    },
    {
        'date': '2026-08-25', 'source': 'TechPowerUp Forums', 'keyword': 'ThermalProtect', 'match': '留言',
        'title': 'hypothetically..... what is a really good PSU for my system?',
        'summary': 'Sol_Badguy 在討論串中說明 Corsair ThermalProtect 的告警指示方式：接頭端子附近的線材顏色會隨溫度由白轉黃、轉橙、再轉棕色，可用以肉眼判斷是否曾觸發保護；並引用 Corsair 官方技術頁的 FAQ「若觸發，是否代表已有零件受損」。',
        'comments': 'Sol_Badguy 另回覆較早的留言，說明目前沒有原生 12V-2x6 插座的舊款（Type 4）Corsair PSU 使用者暫時無法受惠於 ThermalProtect，但表示原廠正在準備相容版本，尚無公開時程；這是留言者轉述，非官方公告連結。',
        'url': 'https://www.techpowerup.com/forums/threads/hypothetically-what-is-a-really-good-psu-for-my-system.351844/post-5775292'
    },
    {
        'date': '2026-08-20', 'source': 'TechPowerUp Forums', 'keyword': 'ThermalProtect', 'match': '留言',
        'title': 'Close call... 5090 Burnt Cable',
        'summary': '連續留言討論 ThermalProtect 的侷限：Dr. Dro 轉述另一位使用者不滿意 ThermalProtect，理由是其溫度觸發點不夠精確；kazuviking 補充即使是 8-pin 接頭，若採用與 12V-2x6 相同的 PCB 排列方式一樣會熔損，只是功率餘裕較大（約多 250W）才較不易發生。',
        'comments': 'Space Lynx 則從成本角度估算：若已發生熔損，送第三方維修約 300～400 美元換電源相關區域，加上另購電源與約 25 美元的 Corsair ThermalProtect 線材，總計約 600 美元，仍比放任風險划算；這是留言者個人估算，非報價單或統計數據。',
        'url': 'https://www.techpowerup.com/forums/threads/close-call-5090-burnt-cable.334508/post-5772336'
    },
    {
        'date': '2026-08-26', 'source': 'TechPowerUp Forums', 'keyword': 'ROG Equalizer', 'match': '留言',
        'title': 'Close call... 5090 Burnt Cable',
        'summary': 'kazuviking 指出，Nvidia 隨 Founders Edition 顯卡附贈的「章魚頭」8-pin 轉接器，內部其實也有類似 ROG Equalizer 的橋接式均流設計，但他認為做工不如 ASUS 版本。',
        'comments': 'rusty caterpillar 僅以一句玩笑回應（「a bridge too far」），沒有提供實測或故障資料佐證兩者橋接設計的實際差異，因此只能視為留言者個人比較觀點，不是對照測試結論。',
        'url': 'https://www.techpowerup.com/forums/threads/close-call-5090-burnt-cable.334508/post-5776023'
    },
    {
        'date': '2026-08-16', 'source': "Tom's Hardware Forums", 'keyword': 'WireView', 'match': '留言',
        'title': 'Power Supply and 12vHPWR',
        'summary': '留言者在討論 12VHPWR 供電疑問時表示該接頭標準「一團亂」，即使用最新標準線材仍可能燒毀，並推薦高階顯示卡加裝 Thermal Grizzly WireView Pro 2，但同時指出價格偏貴。',
        'comments': '本頁沒有更多留言可核讀，屬單則選購建議，沒有觸發或長期使用資料。',
        'url': 'https://forums.tomshardware.com/threads/power-supply-and-12vhpwr.3899315/post-23651390'
    },
    {
        'date': '2026-08-08', 'source': "Tom's Hardware Forums", 'keyword': 'WireView',
        'keywords': ['WireView', 'Ampinel'], 'match': '留言',
        'title': 'Is there a 12V-2X6 Type A to Type B adapter?',
        'summary': '發文者詢問是否有 12V-2x6 Type A 轉 Type B 的轉接器；留言者 Lutfij 回覆不建議额外加裝轉接器，理由是會增加一個新的故障點，並建議如果真的需要監控或保護，應該直接選用 Aqua Computer Ampinel 或 Thermal Grizzly WireView Pro，否則應考慮更換顯示卡本身。',
        'comments': '本頁沒有進一步實測或故障案例，屬留言者的一般性選購建議，理由與既有「多一個轉接點＝多一個風險點」的論述一致。',
        'url': 'https://forums.tomshardware.com/threads/is-there-a-12v-2x6-type-a-to-type-b-adapter.3898886/post-23648685'
    },
])

# Reddit catch-up（同一批 2026-09-02 refresh 的後續）：上一版曾誤判 Reddit 匿名搜尋需要登入才能用；
# 實際核對後發現問題出在 sort=new 參數本身失效（不論是否登入都會跳轉回與關鍵字無關的
# r/all 最新內容），移除該參數、改用純 relevance 排序（必要時加上 subreddit 限定 +
# t=month/t=week）即可取得真實搜尋結果。已用此方式核讀 11 個關鍵字，逐篇讀過主文與可見留言。
rows.extend([
    {
        'date': '2026-08-18', 'source': 'Reddit', 'keyword': 'GPU Tweak III Auto-Shutdown',
        'keywords': ['GPU Tweak III Auto-Shutdown', 'ROG Equalizer'], 'match': '標題＋內文＋留言',
        'title': 'ASUS adds another 12V-2x6 safeguard, GPU Tweak III can now automatically shut down your PC',
        'summary': '貼文轉貼 VideoCardz 對 ASUS GPU Tweak III v2.1.8.0 新增自動關機功能的報導：搭載 Power Detector+ 的 ROG Astral／ROG Matrix 顯示卡在偵測到持續過電流時可自動關機。',
        'comments': '留言核心集中在適用範圍的疑問：多人指出功能需要「正確的 PSU＋GPU 組合」，並非任何 ASUS 顯示卡都支援，僅限具備 Power Detector+ 硬體的 ROG Astral／ROG Matrix 機型，並非泛用於整個 5 系列。另一路討論質疑「連接器不是全貌」——批評 Nvidia 公版設計拿掉了逐 pin 監控與熱關機機制，各板卡廠只能各自加裝專屬方案彌補；也有留言建議可監控 12VHPWR 電壓驟降作為輔助判斷訊號。其餘留言延伸科普 12VHPWR（每 pin 約 100W）與傳統 8-pin（每 pin 約 50W）的承載差異，屬背景知識，非本篇官方數據。',
        'url': 'https://www.reddit.com/r/nvidia/comments/1vqwy4q/asus_adds_another_12v2x6_safeguard_gpu_tweak_iii/'
    },
    {
        'date': '2026-08-27', 'source': 'Reddit', 'keyword': 'Ampinel', 'match': '標題＋內文＋留言',
        'title': 'Free Aquacomputer Ampinel for reviewer',
        'summary': '發文者表示購入 Ampinel 初期使用結果不錯，但逐漸擔心自身 QC 問題——它本身若與 GPU 接觸不良，反而會製造出它原本要偵測的那種風險（用一個新故障點去偵測故障）。他決定換成 WireView Pro II Wired 版，且不想直接轉賣或丟棄，想找英國當地可信的 YouTube 評測者做拆解與風險分析。',
        'comments': '留言者 Ronnie_coleman_light 表示看過其他使用者回報退縮 pin、接頭覆蓋膠水，朋友的裝置確實熔損過。發文者拆下後續更新：確認有 3 根明顯退縮 pin、1 根輕微退縮，確認拿到的是 Rev.4；留言指出 Rev.4 問題已知，Rev.5 改用鍍金 pin 且不會退縮，但原廠並未召回舊批。另一位留言者 remcenfir38SPL 質疑退縮不必然代表故障，要求並取得照片佐證。留言中也建議應先聯繫 Aqua Computer 官方處理，並提及 Gamers Nexus 可能有興趣關注此案例；這些是使用者個人經驗與建議，不是原廠故障率統計。',
        'url': 'https://www.reddit.com/r/watercooling/comments/1vzqn6s/free_aquacomputer_ampinel_for_reviewer/'
    },
    {
        'date': '2026-08-31', 'source': 'Reddit', 'keyword': 'WireView', 'match': '標題＋內文＋留言',
        'title': 'WireView Pro 2 Wired',
        'summary': '發文者延續先前貼文（多次不平衡警告與線材問題）的後續：為了讓顯示卡改成直立安裝，換成 WireView Pro 2 Wired 版。他向同樣使用 MSI PSU 的朋友借了另一條線材後，各 pin 電流分布明顯改善；令他意外的是，連自己另外新買的 MODDIY 線材也出現電流分布不均，換成另一條全新線材後才恢復正常——顯示「全新線材」本身也可能不符規格，不只是舊化或損傷線材才會觸發不平衡警告。他也附上直立安裝走線照片，因為原本能參考的資料很少。',
        'comments': '一名留言者表示自己也是同款機殼＋直立安裝＋WP2，肯定監控帶來的安心感。另一位 RTX 5090 AORUS MASTER 使用者提醒：該卡用的是散熱膏／膠而非墊片，長期直立安裝可能導致膏體滲漏或幫浦效應，雖聽聞後期批次已改善，仍建議謹慎；同時分享自己降壓超頻、降低功耗上限＋加裝 WireView Pro 2 的做法。其餘留言為安裝托架鎖點的技術問答，確認可直接利用顯卡本身的防彎托架螺孔固定。',
        'url': 'https://www.reddit.com/r/ThermalGrizzly/comments/1w2v5v1/wireview_pro_2_wired/'
    },
    {
        'date': '2026-08-31', 'source': 'Reddit', 'keyword': 'WireView', 'match': '標題＋內文＋留言',
        'title': 'WireView Pro II worth for 9070 XT on Linux?',
        'summary': '發文者持有 AMD Radeon RX 9070 XT Nitro+（原廠 330W，最高 TDP 達 363W；他已限制到 250W，因為曾在監控工具中看到瞬間超過 450W 的尖峰），詢問是否值得為這張非 Nvidia 顯示卡加裝 WireView Pro II，以及是否一定要搭配軟體才能使用。',
        'comments': '留言者 std10k 原本以為熔損只會發生在 Nvidia 12VHPWR，但在確認自己的 9070XT 沒事的同時，其 RTX 5090 系統卻曾真的觸發煙霧警報器；他也提到剛入手的 WireView 已測到有一根 pin 已在臨界邊緣，即使已用最好的硬體與線材。發文者與其他留言者補充：Sapphire Nitro+、ASRock Taichi 等部分 AMD 板卡同樣採用 12-pin／12V-2x6 接頭，且已有實際熔損案例。留言 The8Darkness 表示自己的 RTX 5090 即使刻意降壓降頻、功耗壓到 300–350W 仍熔損；但 Brembars 提出反駁，認為那種功耗下熔損多半是插接不確實或線材品質差，而非電源供應器與監控器的問題，雙方沒有共識。rEToRaGeONE 說明社群已有非官方 Linux 版軟體（由 u/Mad4Keebs 提供連結），並澄清軟體並非必要——裝置出廠時已內建安全門檻，只要維持原廠設定，GPU 若故障仍可申請保固；同時提醒 9070XT、其他採多組 8-pin MiniFit-Jr 的 Radeon，以及部分中階 Nvidia 顯示卡都已有熔損案例，建議加裝 WireView 或至少定期用電流鉗表抽查，並附帶提及 Corsair ThermalProtect（65°C 雙金屬開關斷電）作為替代方案。',
        'url': 'https://www.reddit.com/r/ThermalGrizzly/comments/1w2xjye/wireview_pro_ii_worth_for_9070_xt_on_linux/'
    },
])

# 使用者回報漏掉 https://www.reddit.com/r/nvidia/comments/1w0ebt5/ 後追查發現：
# 原因是 GPU Shield 的搜尋詞用了 "GPU Shield" 12V-2x6（加了額外限定詞）；Reddit 搜尋是
# 嚴格逐字 AND 比對，這篇貼文全文只講「12V pin」「connector」，從未出現「12V-2x6」字面，
# 因此被誤判排除，而非真的沒有討論。改回只用產品名本身（不加額外限定詞）重新查核後，
# 除了這篇也一併找到另一篇同日新發的相關貼文。已用同樣方式覆核 T-Guard／TempGuard／
# OptiGuard 是否也受影響：T-Guard 因為是通用詞（會混進育兒防吸吮、籃球「防守」等大量
# 雜訊），拿掉限定詞反而找不到目標內容，代表原本加 GIGABYTE 限定詞是必要且沒有誤刪；
# TempGuard、OptiGuard 拿掉限定詞後沒有找到新內容，原查詢沒有問題。
rows.extend([
    {
        'date': '2026-08-28', 'source': 'Reddit', 'keyword': 'GPU Shield', 'match': '標題＋內文＋留言',
        'title': 'Cooler Master GPU Shield, installed on a 5090D',
        'summary': '發文者在 RTX 5090D（中國市場特規版）上實裝 Cooler Master GPU Shield，說明它會監控每一路 12V pin，任一路超過 15A 便切斷電源；另外接頭上還有一顆溫度探頭，偵測到 60°C 會直接關閉整台電腦。',
        'comments': '發文者在留言補充完整分級行為：單 pin 低於 9A 綠燈、9–12A 閃紅燈、12–15A 恆亮紅燈＋蜂鳴器並在 3 分鐘後切斷、超過 15A 立即切斷。留言 CiobanuXashi 指出這種逐 pin 門檻優於監控總功率，因為熔損通常是單一接點承擔了全部負載，只看總瓦數看不出來。留言者 popsikohl 分享自己在 Mini-ITX 機殼用 Corsair ThermalProtect 線材也有類似效果，機殼摸起來燙但線材沒觸發過。價格確認為 359 人民幣（約 50 美元）。也有留言質疑 60°C 門檻是否過低、可能被 GPU 本身餘溫誤觸發，發文者表示自己用了一年半沒誤觸發過、系統溫度偏低。多則留言延伸批評 Nvidia 連接器設計本身（例如沒有內建 load-balancing 電路）才是根本問題，這類保護只是「業界自己製造問題、再自己賣解法」。',
        'url': 'https://www.reddit.com/r/nvidia/comments/1w0ebt5/cooler_master_gpu_shield_installed_on_a_5090d/'
    },
    {
        'date': '2026-09-02', 'source': 'Reddit', 'keyword': 'GPU Shield', 'match': '標題＋內文＋留言',
        'title': 'Cooler master gpu shield adapter cable unboxing (359 rmb ~= 53 usd)',
        'summary': '發文者在台灣入手中國約三週前上市的 Cooler Master GPU Shield，因手邊顯卡在保固中／只有 5080，暫時無法實測；他特別指出這款轉接器本身保固僅 1 年，但真正重要的是「保護的 GPU 若因接頭熔損而受損，可獲 3 年全額理賠」——這項保險目前只隨中國版販售提供，他不確定會不會全球上市，並拿 Thermal Grizzly（WireView）號稱全球保固的做法對比。另外抱怨包裝內附的是魔鬼氈固定墊，而非直接多鑽幾個螺絲孔。',
        'comments': '留言 DesignerMaximum4770 質疑「這不就是把一條 12VHPWR 變成三條」；no-sleep-only-code 附和認為這只是多一個故障點，尤其原本最大問題就是接頭沒插緊；superman_king 反駁：多一個故障點但有警示與安全斷電，好過只有一個故障點、唯一警告卻是燒卡本身。另有留言希望線材末端能做成直角接頭以解決側板卡住的問題，並提到 Seasonic 有不錯的 90 度接頭方案但偏貴；也有留言呼籲應該發起全球集體訴訟。這些是留言者觀點與期待，沒有實際保護觸發測試。',
        'url': 'https://www.reddit.com/r/overclocking/comments/1w4rvzs/cooler_master_gpu_shield_adapter_cable_unboxing/'
    },
])

# PCGH Extreme（extreme.pcgameshardware.de）：站內 /search/ 表單搜尋（依日期排序），
# 逐篇核讀後新增。搜尋涵蓋 WireView、Ampinel、Equalizer；Ampinel 沒有新內容，
# Equalizer 因為是通用詞（音響等化器）雜訊過多、8 月起沒有專屬新內容可核對。
rows.extend([
    {
        'date': '2026-08-21', 'source': 'PC Games Hardware Extreme', 'keyword': 'WireView', 'match': '標題＋內文',
        'title': 'RTX 5090 trifft auf Thermal Grizzly Wireview Pro II in der Wired Version',
        'summary': '發文者的 Aqua Computer Ampinel 使用約半年後，近兩週開始只要 RTX 5090 進入高負載就重複出現電流差過大警報：他多次檢查所有接點、換上原廠 12V-2x6 線材（PSU 隨附兩條）都沒有改善，某個 pin 在負載幾分鐘後會掉到 0A（其餘接點仍顯示綠燈），因而判斷是 Ampinel 本體問題，準備送回原廠檢測；他推測是裝置重量加上溫度變化，使其在插槽中的固定力道逐漸鬆動（GPU 端插槽本身仍插得很緊）。因此改用 WireView Pro II Wired 版替代，主要考量是可用線材把感測本體與 12V-2x6 接頭分離、避免額外重量直接壓在插槽上；並附上與 Ampinel Typ B 的體積比較照片、溫度感測貼片安裝位置，以及開機、韌體更新、Furmark 測試後「數值皆恢復正常」的結果。',
        'comments': '截至查核時尚無其他使用者留言；發文者自稱會持續更新使用心得（原文結尾「To be continued...」）。',
        'url': 'https://extreme.pcgameshardware.de/threads/rtx-5090-trifft-auf-thermal-grizzly-wireview-pro-ii-in-der-wired-version.677226/'
    },
    {
        'date': '2026-08-24', 'source': 'PC Games Hardware Extreme', 'keyword': 'WireView',
        'keywords': ['WireView', 'ThermalProtect', 'Ampinel'], 'match': '留言',
        'title': 'High Power Stecker defekt?',
        'summary': '主文為使用者 DarthTobi 詢問自己的 12VHPWR 接頭照片是否有燒黑／異常，並反映遊戲中當機次數增加；留言者協助判讀照片並解釋接頭本身脆弱的原因：因為 12VHPWR 的 pin 較小，固定用的金屬夾持結構也較弱，若線材彎折時內外側因彎曲半徑不同互相擠壓，足以讓 pin 從接頭中被拉出約 0.5–1mm，改變接觸電阻並讓其餘 pin 承擔更多電流。',
        'comments': '留言者 QIX 在此附帶提到，自己那條線材最近才因為「把 Ampinel 換成 WireView II wired」而拆下重新收納、單純用手彎折拍照，該線材先前已在顯卡上掛了 1.5 年；另一位留言者 theGucky 則分享自己僅用一條 Corsair（ThermalProtect 類型）轉接線已經用了 3 年（2023 年至今）、歷經 6～7 次插拔與更換顯卡／機殼，從未發熱。這些是旁及提及的長期使用經驗，主文本身的接頭是否真的過熱／燒損，留言者意見不一，沒有最終定論。',
        'url': 'https://extreme.pcgameshardware.de/threads/high-power-stecker-defekt.677281/'
    },
])

# 2026-09-09 weekly refresh：TechPowerUp 用「Newer than」欄位直接篩選 2026-09-02 之後、
# 依日期排序，逐一核讀全部 11 個關鍵字；Reddit 用 subreddit 限定＋t=week 核讀 WireView。
# PCGH Extreme 這次因網站彈出的訂閱／廣告同意視窗導致頁面渲染卡住，未能查核，留待下次。
rows.extend([
    {
        'date': '2026-09-08', 'source': 'TechPowerUp Forums', 'keyword': 'WireView', 'match': '留言',
        'title': 'DLSS 5 Testing Ends in a Melted RTX 5090 Connector, Power Shoots Past 600 W',
        'summary': '主文轉貼 VideoCardz 報導：一名讀者在《NBA 2K27》測試 DLSS 5 神經渲染時，MSI GeForce RTX 5090 Gaming Trio OC 的功耗從約 450W 衝到超過 600W（GPU-Z 峰值讀到 613.5W，且維持穩定而非短暫尖峰，已超過該卡 575W 額定），隨後顯卡停止運作並聞到燒焦味，發現接頭塑膠已熔化並與插座熔合。這是第一起明確歸因於 DLSS 5 額外功耗的熔損案例。',
        'comments': '留言 Chrispy_ 提出技術論點：WireView 1 與 WireView 2 的硬體資料已經證明，這類熔損的成因是一根「已完全正確插入」、額定 9.5A 的 pin 卻流過 25A 以上電流，屬於電源供電迴路缺乏電流平衡機制的設計缺陷，而非接頭本身（Amphenol Microtek 接頭已有 35 年跨產業可靠紀錄）的問題；他認為 Nvidia 把接頭當成代罪羔羊，藉此迴避自家 PCB 成本刪減設計的責任。這是留言者依據 WireView 逐 pin 電流資料做出的技術推論，並非官方故障分析報告。',
        'url': 'https://www.techpowerup.com/forums/threads/dlss-5-testing-ends-in-a-melted-rtx-5090-connector-power-shoots-past-600-w.352412/post-5786049'
    },
    {
        'date': '2026-09-03', 'source': 'TechPowerUp Forums', 'keyword': 'WireView',
        'keywords': ['WireView', 'ROG Equalizer', 'GPU Tweak III Auto-Shutdown', 'ThermalProtect'],
        'match': '標題＋內文＋留言',
        'title': 'Hardware Unboxed Falls Victim to Melted RTX 5090 Power Connector as Cable Reaches 175°C',
        'summary': '主文報導知名評測頻道 Hardware Unboxed 的測試機台（ASUS ROG Astral RTX 5090 搭配 be quiet! Dark Power 13）發生 12V-2x6 熔損：主持人 Steve 是摸到線材發燙才發現異常，熱像儀量到超過 150°C、最高約 175°C。Thermal Grizzly WireView Pro 立即測到根本原因：嚴重電流不平衡，部分 pin 幾乎沒有電流，單一線路卻承載約 22A。損傷主要出現在 PSU 端接頭（需要用鉗子才能拔出熔合的線材），GPU 端接頭外觀正常；Hardware Unboxed 表示線材已完全插妥，不歸咎於安裝問題。',
        'comments': '留言 kazuviking 指出 Hardware Unboxed 手邊其實有 WireView 2，但當時沒有使用，並認為若接了 ROG Equalizer 應也能預防此事。Carlyle2020hs 說明技術細節：ROG Astral 本身已內建逐 pin 電流感測（不論搭配哪種線材），且自韌體更新後可在電流超過可設定門檻、經過一段可設定時間後自動關機（即 GPU Tweak III Auto-Shutdown）；若再接上 ROG Equalizer 線材，還可以提高關機前的電流上限。他也追問：這張 Astral 加上 GPU Tweak III v2.1.8.0，理論上也能觸發同樣的自動關機，這次事故中該功能是否未生效或未啟用（留言中沒有定論）。另一路討論圍繞 ThermalProtect：Dr. Dro 表示自己換 PSU 時直接跳過原廠線材、改用 ThermalProtect，並認為其「感測到高溫即斷開 sense pin」的簡單設計可靠性最高；Space Lynx 指出本次損傷主要在 PSU 端，因此呼籲要有兩端都具備感測、且感測點更靠近端子的 ThermalProtect 版本；Dr. Dro 進一步提出理想方案：結合 Equalizer 的兩端 busbar 與 ThermalProtect 的斷電機制。這些是使用者對既有保護方案適用範圍的技術討論，沒有人實際重現或驗證這次事故本身的自動關機是否觸發。',
        'url': 'https://www.techpowerup.com/forums/threads/hardware-unboxed-falls-victim-to-melted-rtx-5090-power-connector-as-cable-reaches-175%C2%B0c.352273/'
    },
    {
        'date': '2026-09-07', 'source': 'Reddit', 'keyword': 'WireView', 'match': '標題＋內文＋留言',
        'title': 'WireView Pro 2 fan started grinding today',
        'summary': '發文者表示 WireView Pro 2 原本運作良好，某天開機時突然聽到風扇發出研磨聲，聯繫客服後先把風扇關閉；他也提醒其他使用者留意這個潛在問題。',
        'comments': '至少兩名其他使用者回報相同狀況：一人也收到原廠承諾寄送新風扇，並反問風扇對整體監控功能是否關鍵（其裝置本身溫度不高，約 50°C）；另一人表示自己有 3 台裝置，全部在使用幾個月後都開始出現異音。Thermal Grizzly 官方代表 Grizzly_Erik 在串內回覆，說明整體 RMA 率低於 1%，強調在真實生產流程（零件公差、供應商、組裝、運輸）下無法保證每一台都完全無瑕；並指出願意在網路上發文抱怨的多是遇到問題的使用者，大量正常運作的使用者通常不會特別發文，因此討論串中的負面案例比例不能直接當作整體故障率。這是原廠對已知風扇異音問題的公開說明，不是獨立第三方的故障率統計。',
        'url': 'https://www.reddit.com/r/ThermalGrizzly/comments/1w909u4/wireview_pro_2_fan_started_grinding_today/'
    },
    {
        'date': '2026-09-08', 'source': 'TechPowerUp Forums', 'keyword': 'EZDIY-FAB Alpha TS13',
        'match': '標題＋內文＋留言',
        'title': 'EZDIY-FAB Alpha TS13',
        'summary': 'TechPowerUp 站方人員 W1zzard 親自撰寫評測：EZDIY-FAB Alpha TS13 是 U 型 12V-2x6 直通轉接器，內建 TFT 螢幕在不需軟體的情況下即時顯示 GPU 功耗與接頭溫度，超過 85°C 會發出警報；評測以 600W 負載並用熱風槍加熱測試，確認警報確實會觸發。',
        'comments': '留言者 Erratic4^2 表示肯定這個裝置的構想與整體評價，但認為如果要花大錢組頂級主機，他仍寧願多花錢買有逐 pin 監控的 Thermal Grizzly WireView Pro II，並表示自己已經買了。另一位留言者 phanbuey 附和表示自己也是相同想法。留言者 roman 則從量測方法角度提出質疑：評測用分流電阻＋類比數位轉換器量測電流，準確度需要用已知誤差的儀器驗證，建議應改用 TRUE RMS 電流鉗表或搭配示波器的電流探棒（他提到 igorslab 有這類設備）才能驗證讀值是否準確；這是留言者對評測方法論的技術意見，不是對產品本身故障或觸發效果的評論。',
        'url': 'https://www.techpowerup.com/forums/threads/ezdiy-fab-alpha-ts13.351975/'
    },
])

# PCGH Extreme 補查（使用者處理完網站訂閱／廣告同意視窗後）：站內 /search/ 表單，
# 「Neuer als」= 2026-09-02、依日期排序，核讀 WireView。
rows.extend([
    {
        'date': '2026-09-07', 'source': 'PC Games Hardware Extreme', 'keyword': 'WireView',
        'match': '標題＋內文＋留言',
        'title': 'DLSS 5 schuld? Nutzer berichtet von geschmolzenem Stromstecker seiner RTX 5090',
        'summary': 'PCGH 編輯部整理讀者投稿：一名使用者的 RTX 5090 出現熔損接頭，懷疑是啟用 DLSS 5 後功耗遠超上限所致；這是同一起 TechPowerUp 已報導的 DLSS 5 熔損事件，在德語論壇的對應討論。',
        'comments': '留言 u78g 分享自己用 WireView 2 Pro 量到的類似現象：在 LM Studio 跑 AI 推論、token 生成超過約 30 秒後，六路中有兩路電流衝到約 10A，其餘四路只有 4–5A，總功耗顯示 400–430W，且換不同 PSU 或轉接器結果都一樣；他推測若 DLSS 5 讓 VRAM 大量負載但 GPU 核心負載相對較低，可能出現類似的電流分配不均。留言 QIX 建議 Founders Edition 使用者改用 WireView Pro II 的 Wired 版，可自由固定在機殼內、避免裝置重量直接壓在插座上，並表示自己兩種版本都有。留言 Nobbi56 澄清一個常見誤解：並非一定要 ATX 3.1 電源才能用 12V-2x6／12VHPWR，一般 ATX 2.x 電源搭配轉接器也能正常供電，3.0（12VHPWR）與 3.1（12V-2x6）接頭唯一差異只在 sense pin 配置；他也指出已有多起使用 ATX 3.1 電源仍熔損的案例，其中包含一位知名 YouTube 頻道，該頻道甚至擁有廠商贊助的 WireView Pro，卻因為覺得「不會發生在自己身上」而沒有使用——這與 TechPowerUp 上關於 Hardware Unboxed 事件的留言描述相符，應屬同一起事件的跨論壇轉述。留言 DevouringKing 則從成本角度質疑：RTX 5090 已經逼近 6000 歐元，另外加購保護裝置的必要性見仁見智，並以自己的 RX 7900 XT（不到 400 歐元）對比。',
        'url': 'https://extreme.pcgameshardware.de/threads/dlss-5-schuld-nutzer-berichtet-von-geschmolzenem-stromstecker-seiner-rtx-5090.677607/'
    },
])

# 2026-09-16 weekly refresh：TechPowerUp 用「Newer than」= 2026-09-08、依日期排序，
# 逐一核讀全部 12 個關鍵字；Reddit 針對 TempGuard 事件追查原始貼文；PCGH Extreme 用
# 「Neuer als」= 2026-09-08 核讀 Ampinel／GPU Shield。GPU Tweak III Auto-Shutdown、
# Titanload、T-Guard、OptiGuard、GPU Safeguard 本次查核沒有找到新內容。
rows.extend([
    {
        'date': '2026-09-12', 'source': 'TechPowerUp Forums', 'keyword': 'GPU Shield',
        'keywords': ['GPU Shield', 'WireView', 'ROG Equalizer', 'Ampinel', 'ThermalProtect'],
        'match': '標題＋內文＋留言',
        'title': 'Cooler Master GPU Shield Adapter Officially Launches in the US',
        'summary': 'Cooler Master GPU Shield 轉接線正式在美國上市，售價 49.99 美元；先前已於 2026 年 8 月初在中國上市，2026 CES 曾首次亮相。功能為監控電流異常時同時發出聲光警示並主動降低電流，雙色接頭端子設計協助使用者目視確認是否插到底，線長 200mm。',
        'comments': 'Dr. Dro 說明它與 Thermal Grizzly WireView Pro II 的差異：WireView Pro II 有逐 pin 讀數與螢幕，功能更進階；GPU Shield 較接近「智慧型延長線」，加入類似 Astral 系列的電流感測，但不與電腦通訊，且監控門檻是固定的。他也指出中國版提供 3 年保固＋更換保障，全球版僅 1 年產品保固。spartan051 補充：WireView Pro I／II 本身並不會主動平衡逐 pin 電流，只監控溫度與電流。kazuviking 與 Eviling 就 GPU Shield 與 ROG Equalizer 比較：kazuviking 認為 ROG Equalizer 是目前唯一能真正處理 12V-2x6 高故障率的「笨方法」（被動均流），Ampinel 更好但更貴，GPU Shield 之類的裝置只會延後、不會避免熔損；Eviling 則指出 GPU Shield 有蜂鳴器＋斷電功能，而 Equalizer 的斷電功能需另外安裝 Windows 專用軟體（即 GPU Tweak III Auto-Shutdown）才能使用。Sol_Badguy 對 ASUS 官方公布 ROG Equalizer 的 17A 額定提出技術質疑：以接頭端子尺寸換算，17A 相較於 Molex／HCS 業界慣用的安全係數高出約 85%，認為這個數字「過度樂觀」；這是留言者依公開端子規格表換算的個人技術推論，非原廠或第三方的獨立測試結果。',
        'url': 'https://www.techpowerup.com/forums/threads/cooler-master-gpu-shield-adapter-officially-launches-in-the-us.352611/'
    },
    {
        'date': '2026-09-14', 'source': 'TechPowerUp Forums', 'keyword': 'TempGuard', 'match': '標題＋內文＋留言',
        'title': 'ASRock’s TempGuard Failed to Stop a PSU-Side Connector Meltdown on a $15,000 RTX PRO 6000 Rig',
        'summary': '主文轉述一名維修技師的 Reddit 貼文：一套搭載 ASRock Taichi TC-1650T 電源（原生 12V-2x6 線材、內建 ASRock 自家 NTC 溫度感測與 TempGuard 系統）的主機，搭配約 1.5 萬美元的 NVIDIA RTX PRO 6000 Blackwell Workstation Edition 顯示卡，即使兩端接頭都已完全插妥，PSU 端接頭仍熔損並與插座熔合；GPU 端未受損。技師指出感測器裝在線材的接地（ground）側而非應監控的 12V 側，可能是未能即時偵測升溫的原因。主文並提及 TempGuard 過去曾成功攔截一張改裝分流電阻、瞬間拉超過 1300W 的 RTX 5090，避免接頭熔損；同一款 GPU＋PSU 組合先前（今年 3 月）也曾發生類似熔損事故。',
        'comments': '留言 Shrek 質疑「感測器裝錯側」的說法：接地 pin 與 12V pin 同樣會因電流而發熱，未必是感測器位置的問題。Geofrancis 則認為這是設計瑕疵而非單一產品瑕疵：他指出 TechPowerUp 先前的 CES 報導照片已可清楚看到感測器裝在錯誤的一側，並附上該篇報導連結佐證，代表並非只有這次出貨的個別瑕疵。Athena 則推測此事恐怕會導致召回，屬留言者個人臆測。這些是留言者依外部報導與照片做出的推論，沒有原廠正式的根因調查報告可供查核。',
        'url': 'https://www.techpowerup.com/forums/threads/asrocks-tempguard-failed-to-stop-a-psu-side-connector-meltdown-on-a-15-000-rtx-pro-6000-rig.352658/'
    },
    {
        'date': '2026-09-13', 'source': 'Reddit', 'keyword': 'TempGuard', 'match': '標題＋內文＋留言',
        'title': 'ASRock PSU thermal protection fails to prevent melted 16-pin cable on $16,000 RTX PRO 6000 GPU',
        'summary': '此為前述 TechPowerUp 報導所引用的原始 Reddit 貼文，轉貼 videocardz.com 報導：一套 600W RTX PRO 6000 Blackwell 顯示卡在 16-pin 電源線熔入 PSU 插座後仍存活；貼文並提及同一條電源線先前也曾在 GPU 端發生過熔損。',
        'comments': '留言者 underwaterair 從技術角度質疑僅靠溫度感測是否足夠：他引述 Buildzoid 先前的分析，認為問題在於感測探頭與實際發熱點有距離、且不是逐 pin／逐線感測，即使探頭本身正常也可能量不到真正過熱的那一路；他並指出目前所知唯一具備逐 pin 感測的是 ASUS Astral 系列顯卡本身，但預設僅監控、不會主動採取動作，除非使用者自行設定觸發條件。串內多則留言呼籲應直接重新設計接頭或召回顯卡，屬使用者個人立場，非原廠回應。',
        'url': 'https://www.reddit.com/r/ASRock/comments/1wf6dtj/asrock_psu_thermal_protection_fails_to_prevent/'
    },
    {
        'date': '2026-09-10', 'source': 'TechPowerUp Forums', 'keyword': 'EZDIY-FAB Alpha TS13',
        'keywords': ['EZDIY-FAB Alpha TS13', 'Ampinel', 'ThermalProtect'], 'match': '留言',
        'title': 'EZDIY-FAB Alpha TS13',
        'summary': '同一評測討論串本週持續有新留言。outlw6669 認為 Alpha TS13 只是「簡單的早期警示裝置」，除了警報之外沒有主動保護機制，若要花 53 歐元不如加碼買 Aqua Computer Ampinel（約 100 歐元），因為 Ampinel 同時具備監控告警、主動保護與電流均流。Chrispy_ 認為它本質上「只是一台沒有資料記錄的 Thermal Grizzly WireView」，而不是他原先期待、具備數位電位計或 MOSFET 主動均流控制器的裝置；他並指出目前市面上似乎只有 Ampinel 真正取代了 Nvidia 自 40 系列起從設計中拿掉的電流均流電路，且經他搜尋後確認市面上沒有其他類似產品。',
        'comments': 'Claudio 留言力挺 Ampinel，稱其為市場上「唯一能在需要時主動均流」的產品，並表示自己在 5090 上使用、「睡得很安穩」。qlum 則指出 EZDIY-FAB 這類裝置是依電流（而非僅溫度）反應，電流不平衡才是真正的風險來源，因此雖然保護程度較低，仍可能比純溫度感測裝置更有意義，但不確定是否也能保護 PSU 端。串內另有一段 Aleksandar_038 與 Chrispy_ 的長篇交叉討論：Aleksandar_038 主張應由顯卡廠商（他specifically 指 MSI、Asus、Sapphire 等 AIB，而非電源廠）負責；Chrispy_ 則從電力原理解釋：PSU 的職責只是依負載端要求供電並維持電壓，電流監控只能發生在負載端（即 GPU），並非 PSU 該負責的事；Aleksandar_038 其後澄清自己原意是指 AIB 板卡廠，而非電源供應器廠商。這段交叉討論屬於使用者對 12V-2x6 故障歸屬的個人技術論點，沒有原廠或第三方驗證。',
        'url': 'https://www.techpowerup.com/forums/threads/ezdiy-fab-alpha-ts13.351975/post-5786734'
    },
    {
        'date': '2026-09-10', 'source': 'TechPowerUp Forums', 'keyword': 'ThermalProtect',
        'keywords': ['ThermalProtect', 'WireView', 'ROG Equalizer'], 'match': '留言',
        'title': 'Close call... 5090 Burnt Cable',
        'summary': '長期討論串本週新增內容：知名使用者 Dr. Dro 在串中回報自己原生插接的 12V-2x6 接頭，於 600W 負載下量到約 11.65V（電壓降約 2.9%）；留言者 Dragam1337 指出如此明顯的壓降代表可能有異常接觸阻抗，通常與升溫有關（他自己的裝置僅降約 0.1V）。',
        'comments': 'Dr. Dro 說明自己先前嘗試購買 WireView 未成功，目前只有 Corsair ThermalProtect，並表示「唯一能做的是拆下 ThermalProtect、改裝 ROG Equalizer」，但因目前沒有明顯異常訊號、且擔心「越去動它風險越高」，決定先維持現狀觀察。這是單一使用者在缺乏逐 pin 電流資料（如 WireView 可提供）情況下、僅憑電壓量測做出的個人風險判斷，不代表 ThermalProtect 本身有故障，也沒有實際觸發紀錄。',
        'url': 'https://www.techpowerup.com/forums/threads/close-call-5090-burnt-cable.334508/post-5787553'
    },
    {
        'date': '2026-09-11', 'source': 'PC Games Hardware Extreme', 'keyword': 'Ampinel',
        'keywords': ['Ampinel', 'WireView'], 'match': '標題＋內文',
        'title': 'Geforce RTX 5090: 8-Pin-Stromanschlüsse schlagen 12V-2×6（討論串內留言）',
        'summary': '留言者 ParrotHH 在一張二手 Asus TUF RTX 4090 OG OC（原插座插拔不超過約 20 次）上加裝 Ampinel，開機後直接跑 FurMark：Aquasuite 監控軟體顯示 6 路電流中出現約 40% 的不平衡（4.1A 對 7.1A），且 Ampinel 的「Ausgleich／平衡」面板同時顯示有介入動作；但他本人也明確表示「不知道沒有這個調節機制時會是什麼樣子」，並非有無 Ampinel 的前後對照。',
        'comments': 'ParrotHH 隨後刻意搖晃線材、來回移動接頭中的 pin，同一項測試的不平衡明顯改善（電流差從約 3.1A 降到約 0.8A）；但這個改善是接續在「刻意搖晃線材」動作之後出現，較可能是插接觸點狀態改變所致，貼文本身沒有說明是 Ampinel 的均流機制隨時間發揮作用，不能當成「Ampinel 主動均流確實把不平衡修正好」的證據。他認為即使有這樣的不平衡，短期內大機率仍會正常運作，但長期而言這類不平衡通常只會惡化、不會自行改善，是一顆「定時炸彈」。他先前在另一台全新 Corsair 線材上（同樣以電流鉗表量測）也發現類似不平衡，因此推測多數 12V-2x6 接線可能都存在一定程度的不平衡、其中不少已超出規格，只是運氣好尚未出事；這是他個人在兩套系統上的量測與主觀推論，沒有第三方或原廠統計數據佐證。他也提到已為另一台 RTX 5090 FE 主機加購 WireView 2 Pro Wired 版（因為 Ampinel 的外型在該主機裝不下），未來可能一併分享比較結果。',
        'url': 'https://extreme.pcgameshardware.de/threads/geforce-rtx-5090-8-pin-stromanschluesse-schlagen-12v-2-6.677683/post-12147632'
    },
])

# 2026-09-23 weekly refresh：TechPowerUp 用「Newer than」= 2026-09-16、依日期排序，
# 逐一核讀全部 12 個關鍵字；PCGH Extreme 用「Neuer als」= 2026-09-16 核讀
# WireView／Ampinel／ROG Equalizer／ThermalProtect／GPU Shield。Reddit 改以公開搜尋
# 結果與可讀頁面補查，逐篇閱讀 6 筆唯一討論及可見留言；跨版重貼排除。
# GPU Safeguard、OptiGuard、Titanload、T-Guard、GPU Tweak III Auto-Shutdown、
# EZDIY-FAB Alpha TS13（單獨關鍵字搜尋）本次查核沒有找到新內容。
rows.extend([
    {
        'date': '2026-09-20', 'source': 'TechPowerUp Forums', 'keyword': 'ThermalProtect',
        'keywords': ['ThermalProtect', 'ROG Equalizer'], 'match': '留言',
        'title': 'Close call... 5090 Burnt Cable',
        'summary': '長期討論串本週新增內容：JIWIL 詢問自己的 be quiet Dark Power 13（原生 12VHPWR 插座）搭配 RTX 4080 能否使用 ThermalProtect；Dr. Dro 引用 Corsair 官方相容性說明確認可行（12VHPWR 與 12V-2x6 僅 sense pin 標示不同，線材本身無機械差異），並說明 ThermalProtect 與 ROG Equalizer 的差異：ThermalProtect 是符合規格的標準線材（3-dimple 端子夾持設計＋溫度斷開 sense pin），售價約 25 美元；ROG Equalizer 是重型線材（4-spring 端子夾持設計，握持力更好、每線可承載更高電流、較不易過熱），售價約為前者兩倍。他本人兩者都買了，但認為 ThermalProtect 已足夠、且較便宜。',
        'comments': '同一討論串另有留言引用 igorslab.de 的 ROG Equalizer 評測連結，指出 Equalizer 的端子壁厚度仍是「一般厚度」，端子在插槽內仍可上下左右微幅移動；相較之下，有使用者分享自己 Lian Li 電源原廠線材採用端子直接射出成型、幾乎零位移的設計，並認為即使是強化版的 Equalizer 也比不上這種做法，甚至推測未來或許會出現結合 Equalizer 匯流排設計與 Lian Li 剛性接頭的「Equalizer V2」；這是留言者依評測圖片與個人觀察做出的推論，並非官方或第三方的機構強度測試數據。',
        'url': 'https://www.techpowerup.com/forums/threads/close-call-5090-burnt-cable.334508/post-5793615'
    },
    {
        'date': '2026-09-21', 'source': 'TechPowerUp Forums', 'keyword': 'ROG Equalizer',
        'keywords': ['ROG Equalizer', 'ThermalProtect', 'WireView'], 'match': '留言',
        'title': 'Close call... 5090 Burnt Cable',
        'summary': '同一討論串本週延伸：A Computer Guy 提出構想，主張在線材中加入可更換保險絲（每線一顆）作為比 WireView Pro II 更便宜、且不需軟體的替代保護方案。Dr. Dro 回應：以 9.2A/pin 的額定上限來看，固定保險絲恐怕會因正常負載下的短暫尖峰而頻繁跳脫；他認為 ThermalProtect「偵測到過熱就斷開 sense pin」已經足夠，並提出他心目中理想的「終極版」安全線材構想：結合 ROG Equalizer 的高承載設計（兩端都有匯流排、4-spring 端子夾持）與 ThermalProtect 的溫度斷電機制（並讓感測點更貼近端子本體），必要時再加一顆觸發電流設在 12A 以上的可重置保險絲。',
        'comments': '這是 Dr. Dro 個人對「理想保護線材」的設計構想，目前市面上沒有任何一款產品同時具備這些特性，不代表任一現有產品已如此設計，也沒有原型或測試數據佐證這個構想的可行性。',
        'url': 'https://www.techpowerup.com/forums/threads/close-call-5090-burnt-cable.334508/post-5794186'
    },
    {
        'date': '2026-09-19', 'source': 'TechPowerUp Forums', 'keyword': 'ThermalProtect',
        'keywords': ['ThermalProtect', 'ROG Equalizer'], 'match': '留言',
        'title': 'DLSS 5 cause GPU black screen and 100% fans in every games that I tried.',
        'summary': '新討論串：一名 ROG Astral RTX 5090 使用者反映啟用 DLSS 5 神經渲染後，多款遊戲載入完成即當機、風扇衝到 100%，嘗試多種設定（含降壓）都未改善。Dr. Dro 回覆建議：DLSS 5 會顯著推高功耗，Astral 本身也非入門款，呼籲務必仔細檢查兩端接頭是否插妥，因為線材可能已有材料疲勞、加上這次高功耗成為額外壓力；由於該使用者的電源已有原生 12VHPWR/12V-2x6 插座，他建議直接添購 Corsair ThermalProtect 或 ROG Equalizer 線材，「安全總比後悔好」。',
        'comments': '這只是預防性建議，串內截至查核時沒有後續回報是否真的是連接器問題、也沒有加裝保護線材後的追蹤結果。',
        'url': 'https://www.techpowerup.com/forums/threads/dlss-5-cause-gpu-black-screen-and-100-fans-in-every-games-that-i-tried.352696/post-5793196'
    },
    {
        'date': '2026-09-19', 'source': 'TechPowerUp Forums', 'keyword': 'EZDIY-FAB Alpha TS13', 'match': '標題＋內文',
        'title': 'My mini-ITX project.',
        'summary': 'TechPowerUp 論壇成員 AVATARAT 發表完成的 mini-ITX 改裝文，將既有 RTX 5090 系統整套移植進小型化機殼；文中提到最後裝上的零件是 EZDIY-FAB Alpha TS13，這是第二次下單才順利到貨（第一次出貨因海關以「不明原因」退回）。完工貼文本身未再提及 Alpha TS13 實際運作中的顯示或告警內容。',
        'comments': '這則貼文沒有提供 Alpha TS13 運作中的功耗或溫度讀值，只確認裝機完成、克服海關延誤後順利安裝這一件事，不能當作產品運作效果的證據。',
        'url': 'https://www.techpowerup.com/forums/threads/my-mini-itx-project.352847/'
    },
    {
        'date': '2026-09-21', 'source': 'PC Games Hardware Extreme', 'keyword': 'Ampinel',
        'keywords': ['Ampinel', 'WireView'], 'match': '留言',
        'title': 'Geforce RTX 60 wohl erst 2028: Kopite7kimi korrigiert frühere Prognose（討論串內留言）',
        'summary': 'PCGH Extreme 使用者 ParrotHH（即上週 FurMark 測試同一人）本週回覆另一位使用者時提到：他上週提到會為 RTX 5090 FE 加購的 WireView 2 Pro Wired 已經裝上，目前 4090 用 Ampinel、5090 FE 用 WireView 2 Pro，兩張卡都已加裝監控裝置；他表示自此在兩張卡滿載時「明顯更安心」，並認為對這樣的配置而言，約 110 歐元的花費是值得的。',
        'comments': '這則貼文沒有提供新的電流量測數據，純粹是延續上週裝置採購計畫的完成確認與主觀使用心得，不能當作監控或均流效果的量化證據。',
        'url': 'https://extreme.pcgameshardware.de/threads/geforce-rtx-60-wohl-erst-2028-kopite7kimi-korrigiert-fruehere-prognose.678006/post-12152680'
    },
    {
        'date': '2026-09-16', 'source': 'PC Games Hardware Extreme', 'keyword': 'WireView', 'match': '留言',
        'title': 'Geforce RTX 5090: 16-Pin-Stecker bei 2D-Spiel stark verschmort',
        'summary': 'PCGH 編輯部報導一起案例：一張 PNY GeForce RTX 5090 的 16-pin 電源接頭嚴重熔損，但事發時系統僅在跑 2D／低負載內容，非高負載遊戲或壓力測試；機主反映 PNY 客服拒絕受理保固；報導本身承認目前缺乏量測數據可以確認熔損成因。',
        'comments': '留言者 Zandalor01 提出技術解讀：他引述 IgorsLab、der8auer 等分析者的見解，認為這類熔損多半與瞬時負載高低關聯較小，主因是接頭本身端子數量偏少、公差偏大、材料抗磨耗設計不足，導致個別 pin 接觸電阻升高、逐漸發熱惡化，即使在低負載下也可能發生；因此建議使用者盡量做到「插一次就不要再拔動」以減少磨耗。他也提到 der8auer 的 WireView 轉接器或許有助於監控與緊急斷電，但特別提出一個尚未在本報告見過的疑慮：即使 WireView 事先偵測到異常、或事後能佐證是接觸不良而非使用者過失，顯卡廠商仍可能反過來主張「問題出在 WireView 本身」而拒絕受理保固——這是留言者個人推測的風險，目前沒有真實案例可佐證廠商是否真的會這樣認定。',
        'url': 'https://extreme.pcgameshardware.de/threads/geforce-rtx-5090-16-pin-stecker-bei-2d-spiel-stark-verschmort.677842/post-12150096'
    },
    {
        'date': '2026-09-22', 'source': 'Reddit', 'keyword': 'ROG Equalizer',
        'keywords': ['ROG Equalizer', 'WireView', 'GPU Safeguard'], 'match': '內文＋留言',
        'title': 'Update Post (ROG Equalizer with WVP 2)',
        'summary': 'RTX 5080 Astral 使用者將 ASUS ROG Equalizer 與 WireView Pro II 串接；Steel Nomad 兩次測試中，WireView pin 2–6 約 5.3–5.7A、pin 1 約 3.0–3.3A，總電流約 30–31A，WireView OUT 約 50°C（室溫 20°C），功率約 370W。發文者自行注意到約 2.4A 的 pin 差距，但也明確說這不是嚴謹科學測試。',
        'comments': '留言有兩種方向：有人以 5080、最高 pin 未超過 6A 或「約 2.5A 可接受」表示暫時安全，也有人提醒 Equalizer 的 bridge 可能讓 WireView 只看到 bridge 到 GPU 的短段，PSU 到 bridge 的個別電流與阻抗變化未被同樣監控；另有人認為 WireView 增加故障點。發文者重插後回報差距降至約 1.5A。這些是留言者判讀與單機讀值，沒有共同門檻或對照測試。',
        'url': 'https://www.reddit.com/r/ThermalGrizzly/comments/1wi53nd/update_post_rog_equalizer_with_wvp_2/'
    },
    {
        'date': '2026-09-22', 'source': 'Reddit', 'keyword': 'ROG Equalizer',
        'keywords': ['ROG Equalizer', 'WireView', 'GPU Safeguard', 'GPU Tweak III Auto-Shutdown'], 'match': '內文＋留言',
        'title': 'WireView Pro 2 and ROG Equalizer',
        'summary': 'RTX 5080 Astral OC 使用者搭配 ROG Equalizer、Strix 1000W Platinum PSU，因不想長時間開 HWiNFO，詢問在顯卡已有逐 pin 監控時是否仍需要 WireView Pro II。',
        'comments': 'Thermal Grizzly 代表說明：若 Equalizer bridge 位於上游，WireView 只能評估 bridge 到 GPU 的區段，無法看到 PSU 到 bridge 的個別分配，但仍可監控它看得到的區段。留言者另提到 WireView 增加第二個接頭、有人曾遇到第一條量測線／pin 1 燒損而讀值為 0A，以及 GPU Tweak III 可作為不常駐 HWiNFO 的替代；另有 MSI MPG Ai1300TS 使用者偏好把 per-pin 監控整合在 PSU。這些是個案與原廠代表說明，沒有統一的故障率或性能對照。',
        'url': 'https://www.reddit.com/r/ThermalGrizzly/comments/1whd8yh/wireview_pro_2_and_rog_equalizer/'
    },
    {
        'date': '2026-09-20', 'source': 'Reddit', 'keyword': 'GPU Safeguard',
        'keywords': ['GPU Safeguard', 'GPU Shield', 'WireView', 'Ampinel', 'ThermalProtect'], 'match': '內文＋留言',
        'title': 'RTX 5090 owners: Worth upgrading to a thermal-protected 12V-2x6 setup if you’ve had zero issues?',
        'summary': 'RTX 5090 使用者已有約一年無線材問題，仍在 Ampinel、WireView Pro II、Corsair ThermalProtect 與維持現狀之間比較，並擔心水冷背板空間。',
        'comments': '9/20 一名 MSI MPG Ai1300TS 買家說，選 GPU Safeguard+ 是因為本來就要換 PSU、想避免機內增加額外裝置與接頭；他回報 MSI Center 介面清楚、PSU 能裝入機殼，並在 FurMark 將 GPU 從 575W／60°C 降壓到 500W／55°C。這是購買理由與單機降壓結果，沒有 Safeguard+ 實際觸發資料。串內另有 GPU Shield、WireView、Ampinel、ThermalProtect 的偏好爭論，沒有共識測試。',
        'url': 'https://www.reddit.com/r/watercooling/comments/1wihia6/rtx_5090_owners_worth_upgrading_to_a/'
    },
    {
        'date': '2026-09-16', 'source': 'Reddit', 'keyword': 'WireView',
        'keywords': ['WireView'], 'match': '內文＋留言',
        'title': 'WireView Pro II Thermals Question',
        'summary': '水冷系統使用者在 4K 高負載下讓 GPU 持續約 550–580W、45–60 分鐘，回報 WireView GPU IN 約 70°C；多個 pin 約 8.5–9.3A，GPU OUT 約 55°C，因水冷背板導熱條件不同而詢問是否正常。',
        'comments': '留言建議重新插接、確認接點並在 WireView 附近增加風流；原發文者回覆未看到明顯電流不平衡。這是單一水冷系統的溫度與電流讀值，沒有故障或長期壽命結論。',
        'url': 'https://www.reddit.com/r/ThermalGrizzly/comments/1wi64cq/wireview_pro_ii_thermals_question/'
    },
    {
        'date': '2026-09-21', 'source': 'Reddit', 'keyword': 'WireView',
        'keywords': ['WireView'], 'match': '內文＋留言',
        'title': 'Gigabyte RTX 4090 Windforce - Wireview Pro 2 compatibility',
        'summary': 'Gigabyte RTX 4090 Windforce 使用者詢問 WireView Pro II 相容性。',
        'comments': 'Thermal Grizzly 代表回覆，若是 12VHPWR／12V-2x6 顯卡，應選 Wired 版本；串內另提供尺寸圖供使用者確認。這是相容性說明，沒有實際負載或保護效果測試。',
        'url': 'https://www.reddit.com/r/ThermalGrizzly/comments/1wlzsav/gigabyte_rtx_4090_windforce_wireview_pro_2/'
    },
    {
        'date': '2026-09-13', 'source': 'Reddit', 'keyword': 'GPU Safeguard',
        'keywords': ['GPU Safeguard', 'Ampinel', 'WireView'], 'match': '內文＋留言',
        'title': 'What’s currently the best option for protecting a 12vhpwr GPU from melting?',
        'summary': '使用者比較 Ampinel、WireView Pro II 與 MSI MPG Ai1300TS，並提出價格、保固、額外接頭及是否值得更換整台 PSU 的疑問。',
        'comments': '留言分別提到 WireView 的逐 pin 讀值、保固與自動關機腳本，Ampinel 的主動均流，以及 MSI 整合式 PSU 不需外接轉接器；不同使用者對額外接頭、價格與是否能處理根因有不同看法，沒有形成共同推薦或對照測試。',
        'url': 'https://www.reddit.com/r/gpu/comments/1wfcl7m/whats_currently_the_best_option_for_protecting_a/'
    },
    {
        'date': '2026-09-28', 'source': 'Reddit', 'keyword': 'WireView',
        'keywords': ['WireView'], 'match': '內文＋留言',
        'title': 'WireView Pro II - 6 Wire Monitoring Gap',
        'summary': '新購買者提出 WireView Pro II 只監控 6 條 +12V 線，但 12 條線都承載電流，因而認為這可能是不完整的監控實作。',
        'comments': '留言說明 12 條中另有 6 條是接地線；回覆者表示 GPU 的主要 12V 功率經由 6 條 +12V 線輸入，接地回流還會經由 GPU、主機板與 PCIe 插槽的多條接地路徑分流，因此接地線電流較低。原發文者後續表示實測接地回流只有一部分，且 +12V 讀值與 WireView 顯示一致。這是該串的技術說明與單機確認，沒有獨立安全門檻測試。',
        'url': 'https://www.reddit.com/r/ThermalGrizzly/comments/1wsukcp/wireview_pro_ii_6_wire_monitoring_gap/'
    },
    {
        'date': '2026-09-28', 'source': 'Reddit', 'keyword': 'WireView',
        'keywords': ['WireView'], 'match': '標題＋內文＋留言',
        'title': 'Going from Regular WV Pro 2 To Noctua Edition?',
        'summary': 'WireView Pro II 使用者詢問是否應從一般版換成 Noctua Edition，以降低未來風扇問題的疑慮。',
        'comments': '留言有人打算把一般版移到另一台電腦，也有人認為約 200 美元的換機成本難以合理化；另有使用者表示一般版風扇正在故障但遊戲與 AI 負載溫度仍正常，且目前沒有新版風扇失效率資料。其他留言指出風扇平常很少啟動，Noctua 版對既有使用者的實際價值尚不明確。',
        'url': 'https://www.reddit.com/r/ThermalGrizzly/comments/1wsh3dj/going_from_regular_wv_pro_2_to_noctua_edition/'
    },
    {
        'date': '2026-09-27', 'source': 'Reddit', 'keyword': 'WireView',
        'keywords': ['WireView'], 'match': '標題＋內文＋留言',
        'title': 'WireView Pro II GPU Noctua Edition is here!',
        'summary': 'Thermal Grizzly 在 r/ThermalGrizzly 宣布 WireView Pro II GPU Noctua Edition 上市；主文要求購買前查核相容清單，但沒有新的電流或溫度實測。',
        'comments': '留言集中在約 80 美元價差、Noctua frameless A4x10 風扇與較大外殼、原版風扇很少啟動、Wired 版預計約 2–3 個月、Linux 支援尚非官方、白色版本，以及 SFF 厚度／相容性。這些是留言者的價格、外觀與相容性意見，不能推成新版已降低多少溫度。',
        'url': 'https://www.reddit.com/r/ThermalGrizzly/comments/1wrh7l1/wireview_pro_ii_gpu_noctua_edition_is_here/'
    },
    {
        'date': '2026-09-27', 'source': 'Reddit', 'keyword': 'WireView',
        'keywords': ['WireView'], 'match': '標題＋內文＋留言',
        'title': 'Is there a way to replace the fan?',
        'summary': 'WireView II 使用者表示風扇啟動時出現很大的磨擦聲，詢問是否應聯絡客服或自行更換。',
        'comments': '留言建議聯絡 Thermal Grizzly 申請更換，並指出原廠有拆解教學；原發文者因此表示想改用 Noctua Edition。另一名留言者說自己的裝置從未聽到風扇啟動，但串內沒有足以估計故障率的樣本或統計。',
        'url': 'https://www.reddit.com/r/ThermalGrizzly/comments/1wrt3eg/is_there_a_way_to_replace_the_fan/'
    },
    {
        'date': '2026-09-27', 'source': 'Reddit', 'keyword': 'WireView',
        'keywords': ['WireView'], 'match': '標題＋內文＋留言',
        'title': 'Which Version to get?',
        'summary': '使用者因垂直安裝 Gigabyte RTX 4090，詢問一般、反向或 Wired 版 WireView Pro II 的選擇。',
        'comments': '留言建議垂直安裝選 Wired 版以保留螢幕可視性，並說明一般／反向版本主要是接頭方向差異；也提到 Wired 版有較多安裝位置，但仍需依顯示卡接頭方向與機殼路徑確認。這是相容性建議，沒有負載或保護效果測試。',
        'url': 'https://www.reddit.com/r/ThermalGrizzly/comments/1wrwyo9/which_version_to_get/'
    },
    {
        'date': '2026-09-24', 'source': 'Reddit', 'keyword': 'OptiGuard',
        'keywords': ['OptiGuard'], 'match': '留言',
        'title': 'RTX 5090 12V-2x6 connector reaches 91.7°C with DLSS 5, 16-pin input peaks at 647W',
        'summary': '主文轉貼一項 RTX 5090 DLSS 5 測試：平均功耗接近 600W、16-pin 接頭量到 91.7°C；同文指出 RTX 5080 低於 53°C。',
        'comments': '留言者分別提出 410W power limit、降壓後約 515–525W 或不使用 DLSS 5 等降低負載方式；也有人認為 90°C 接頭問題不應簡化歸因於 DLSS 5，另有人僅以個人看法推薦 Seasonic OptiGuard。未讀到 OptiGuard 在此事件中的實測或觸發資料。',
        'url': 'https://www.reddit.com/r/nvidia/comments/1wp9dx4/rtx_5090_12v2x6_connector_reaches_917c_with_dlss/'
    },
    {
        'date': '2026-09-28', 'source': 'TechPowerUp Forums', 'keyword': 'WireView',
        'keywords': ['WireView'], 'match': '標題＋內文＋留言',
        'title': 'Thermal Grizzly and Noctua Introduce WireView Pro II Noctua Edition GPU Monitoring Device',
        'summary': 'TechPowerUp 新聞串轉貼 Noctua Edition 發布資料：產品以逐條 12V 導體監控、TFT 顯示、聲音警示及可選自動關機為基礎，並主打較安靜的客製化散熱；官方公布建議售價 189.90 美元／歐元。',
        'comments': '可見留言有人認為 190 美元相對一般版過貴，也有人嘲諷高功耗顯卡需要為接頭加主動散熱；另一則留言提到 WireView 可在不平衡或過熱時關機，並有留言討論原版風扇噪音。這些是論壇反應，官方貼文內的 300W／400W／480W 風扇啟動與噪音數據屬發布資料，不當成使用者實測。',
        'url': 'https://www.techpowerup.com/forums/threads/thermal-grizzly-and-noctua-introduce-wireview-pro-ii-noctua-edition-gpu-monitoring-device.353137/'
    },
    {
        'date': '2026-09-28', 'source': 'Chiphell', 'keyword': 'WireView',
        'keywords': ['WireView', '12V-2x6'], 'match': '標題＋內文＋留言',
        'title': '[PC硬件] 暴力熊、猫头鹰推出 12V-2×6 监控设备 WireView Pro II Noctua Edition：更强散热',
        'summary': 'Chiphell 轉貼 IT之家資料，介紹 WireView Pro II Noctua Edition：整合鋁製散熱片、較大的 Noctua NF-A4x10n 風扇與客製風扇格柵；轉貼內容稱多數時間可停轉，極端測試下風扇啟動所需功耗為原版 2 倍、多個功率點平均低 3°C，400～480W 時公布 10cm 風扇噪音 21.5dB(A)、1m 1.5dB(A)，定價 189.90 美元。以上是轉貼的發布資料，不是 Chiphell 使用者實測。',
        'comments': '可見留言多為負面或懷疑式反應：有人表示這是在替問題接口增加外設，有人批評價格／產品定位，也有人指出這實際上是轉接顯卡供電。留言沒有提供 Noctua Edition 的實機電流、溫度或保護觸發測試，因此不能從本串確認改善幅度或可靠度。',
        'url': 'https://www.chiphell.com/thread-2905450-1-1.html'
    },
    {
        'date': '2026-09-27', 'source': 'Hardwareluxx Forum', 'keyword': 'WireView',
        'keywords': ['WireView'], 'match': '標題＋內文＋留言',
        'title': '[User-Review] Thermal Grizzly Wireview Pro II “Noctua Edition” im Lesertest',
        'summary': 'Hardwareluxx 使用者完整測試 WireView Pro II Noctua Edition：記錄逐線電流監控、TFT 顯示、半主動風扇、溫度感測與自動關機等功能；約 20°C 室溫下模組峰值約 44°C、風扇未自行啟動，強制約 40% 轉速後表面溫度下降約 6°C。這是單一使用者測試，文中也說熱天結果可能不同。',
        'comments': '作者列出的優點包括逐 pin 監控、無軟體自動關機、24 個月延伸保固、可獨立運作、低噪音與相容性清單；缺點是硬體／軟體目前只有英文，以及 Noctua Edition 價格高，作者認為相較一般版約貴 80 歐元，理性上不易合理化。留言者因高價 GPU 與 RMA 爭議表示願意購買，並詢問卡扣可拆性、是否能確認插到底、USB splitter 與軟體負載；作者回覆可用扁平工具拆卡扣、可從側面確認插到底，但 USB splitter 不在配件內。不能把單一測試推成普遍溫度或風扇壽命結論。',
        'url': 'https://www.hardwareluxx.de/community/threads/thermal-grizzly-wireview-pro-ii-%E2%80%9Cnoctua-edition%E2%80%9D-im-lesertest.1382401/'
    },
    {
        'date': '2026-09-28', 'source': 'Hardwareluxx Forum', 'keyword': 'WireView',
        'keywords': ['WireView'], 'match': '內文＋留言',
        'title': 'Thermal Grizzly Lesertest: Testet eine von drei WireView Pro II Varianten!',
        'summary': 'Hardwareluxx WireView Wired 版測試者在安裝主機板電源按鈕 splitter 時，表示小型接頭在正常、仔細按壓下從焊點脫落；他認為該重要接頭固定方式過弱，並附圖詢問原廠。這是單一安裝個案。',
        'comments': 'der8auer 回覆表示理解並道歉，建議直接聯絡客服，會安排更換；測試者後續表示已完成聯絡。留言支持的是換貨處理，不代表已確認普遍設計失效或故障率。',
        'url': 'https://www.hardwareluxx.de/community/threads/thermal-grizzly-lesertest-testet-eine-von-drei-wireview-pro-ii-varianten.1381759/post-31282820'
    },
])

# 2026-10-07 weekly refresh：Reddit 逐篇核讀主文與可見留言；TechPowerUp 以
# Newer than=2026-09-29、依日期排序搜尋產品全名與主要別名，並逐筆核讀有實質
# 使用經驗或產品比較的留言。其他論壇以相同日期範圍與在地用語補查，未找到可新增、
# 且能完整讀取主文與留言的唯一討論。
reddit_discovery_audit.extend([
    ('WireView／GPU Safeguard+／PinProtect+／Ampinel／ROG Equalizer', 'https://www.reddit.com/r/buildapc/comments/1ww7rp7/just_bought_a_5090_how_do_i_prevent_the_melting/', '納入', '5090 FE 使用者比較外接逐 pin 監控與整合式 PSU；完整可見留言已讀'),
    ('WireView／ROG Equalizer', 'https://www.reddit.com/r/ThermalGrizzly/comments/1wt3sdk/wireview_pro_2_makes_me_crazy/', '納入', '反覆不平衡告警、自動關機及與 GPU Tweak 3 讀值差異'),
    ('WireView', 'https://www.reddit.com/r/pcmasterrace/comments/1wvgc0k/the_latest_cutscene_in_the_12v2x6_connector/', '納入', '針對換線能否根治 12V-2x6 熔損的討論'),
    ('WireView', 'https://www.reddit.com/r/ThermalGrizzly/comments/1wu2xtp/wireview_pro_2_compatibility/', '納入', 'Gainward RTX 5080 Phoenix V2 相容性及原廠回覆'),
])
rows.extend([
    {
        'date': '2026-10-03', 'source': 'Reddit', 'keyword': 'WireView',
        'keywords': ['WireView', 'GPU Safeguard', 'PinProtect／PinProtect+', 'Ampinel', 'ROG Equalizer'],
        'match': '標題＋內文＋留言',
        'title': 'Just bought a 5090. How do I prevent the melting cable?',
        'summary': 'RTX 5090 FE 使用者採用 1250W Gold、ATX 3.1 電源與原生 12VHPWR 線，未使用第三方轉接器；因擔心接頭熔損而詢問預防方式。主文本身沒有回報已發生故障。',
        'comments': '留言建議 WireView Pro II、MSI GPU Safeguard+ 或 Corsair PinProtect+。支持 WireView 的留言者描述其可偵測逐 pin 不平衡、指出異常 pin 並自動關機；另一派提醒 WireView／Ampinel 類外接監控器會額外增加兩個 12V-2x6 接頭，也有人指出 WireView Pro II 直插版不適合 5090 FE。ROG Equalizer 被提及但沒有本串實測。這些是選購建議與個人看法，沒有這篇貼文自身的保護觸發結果。',
        'url': 'https://www.reddit.com/r/buildapc/comments/1ww7rp7/just_bought_a_5090_how_do_i_prevent_the_melting/'
    },
    {
        'date': '2026-10-02', 'source': 'Reddit', 'keyword': 'WireView',
        'keywords': ['WireView'], 'match': '內文＋留言',
        'title': 'The latest cut-scene in the 12v-2x6 connector charade!',
        'summary': '發文者引用 Thermal Grizzly／der8auer 對線材因素的影片結論，詢問更換線材究竟能否一次解決問題，或日後仍可能再發生；主文沒有回報自己的接頭故障。',
        'comments': '留言把可能原因分別歸於 GPU 缺乏逐 pin 均流、接頭安全裕度不足、線材／接點電阻及廠商保固政策；另有一名使用者表示同一條線搭配 WireView 約六個月未看到惡化。這些是技術觀點與單機經驗，本串沒有對照測試或根因確認。',
        'url': 'https://www.reddit.com/r/pcmasterrace/comments/1wvgc0k/the_latest_cutscene_in_the_12v2x6_connector/'
    },
    {
        'date': '2026-09-30', 'source': 'Reddit', 'keyword': 'WireView',
        'keywords': ['WireView'], 'match': '標題＋內文＋留言',
        'title': 'Wireview pro 2 compatibility',
        'summary': 'Gainward RTX 5080 Phoenix V2 使用者因相容清單未列該卡，詢問一般版、反向版與 Noctua Edition 是否能安裝。',
        'comments': 'Thermal Grizzly 代表表示「未列入」只代表尚未實體或目視驗證，不等同確定不相容；應依產品技術圖確認接頭周圍散熱器、護罩與機殼淨空，而不是只比較顯卡總長與厚度。代表同時確認 Noctua Edition 外殼較大，尺寸不與一般版相同；另一名 Gigabyte RTX 5080 使用者表示凹入式接頭改用 Wired 版可安裝，但提醒自動關機線仍受主機板前面板接頭形式限制。',
        'url': 'https://www.reddit.com/r/ThermalGrizzly/comments/1wu2xtp/wireview_pro_2_compatibility/'
    },
    {
        'date': '2026-09-29', 'source': 'Reddit', 'keyword': 'WireView',
        'keywords': ['WireView', 'ROG Equalizer'], 'match': '標題＋內文＋留言',
        'title': 'Wireview Pro 2 makes me crazy',
        'summary': '使用者年初替 RTX 5090 與 RTX 5080 各購買一台 WireView Pro II，兩台很快都出現不平衡警告；5090 系統在重新插接、更換線材及先後更換三台 ATX 3.1 電源後仍反覆告警，執行《Control Resonant》時即使降壓、80% 功耗上限、約 380～400W，也曾在一分鐘內觸發自動關機。拔除 WireView 後，GPU Tweak 3 的逐 pin 讀值與溫度看起來正常。',
        'comments': '一名留言者表示自己遇過相同情況，最後判斷是 WireView 接頭本身；另一名留言者認為動態負載下逐 pin 依序取樣可能產生看似不平衡的畫面，建議用 FurMark 穩定負載驗證。原發文者表示已使用最新韌體，且不同遊戲的表現不同；Thermal Grizzly 代表建議限制 FPS 並拉長取樣間隔。串內沒有確認根因究竟是接頭、取樣方式或遊戲負載。',
        'url': 'https://www.reddit.com/r/ThermalGrizzly/comments/1wt3sdk/wireview_pro_2_makes_me_crazy/'
    },
    {
        'date': '2026-10-05', 'source': 'TechPowerUp Forums', 'keyword': 'ThermalProtect',
        'keywords': ['ThermalProtect'], 'match': '留言',
        'title': 'Close call... 5090 Burnt Cable — ThermalProtect 實際關機觸發',
        'summary': '長期討論串中，Dr. Dro 回報前一晚執行 DLSS 5 mod 時，Corsair ThermalProtect 曾觸發關機。',
        'comments': '另一名留言者把這視為線材保護有動作，但同時追問顯示卡狀況；Dr. Dro 只補充該負載在 4K 下會持續拉到功耗上限。串內沒有提供觸發溫度、感測端、事件紀錄或關機後檢查結果，因此可確認的是「曾關機」，不能判定已避免了何種損傷。',
        'url': 'https://www.techpowerup.com/forums/threads/close-call-5090-burnt-cable.334508/post-5803151'
    },
    {
        'date': '2026-10-01', 'source': 'TechPowerUp Forums', 'keyword': 'GPU Shield',
        'keywords': ['GPU Shield'], 'match': '內文＋留言',
        'title': 'ElmorLabs PMD2X Features Per-Wire 12V-2×6 Monitoring With Overcurrent Alarm',
        'summary': '主文介紹 ElmorLabs PMD2X 的逐線電流、功率與電壓監控及可設定聲音警報，並明確把其用途比作 Cooler Master GPU Shield；這是競品比較提及，不是 GPU Shield 本身的新測試。',
        'comments': '留言一方面肯定監控所有線路，另一方面批評又增加接頭、只是補救根本問題，並質疑標示的電流誤差 ±0.5A（10A 時約 5%）與未說明 min／max／average 的量測方法。這些疑慮針對 PMD2X，不應直接套用到 GPU Shield。',
        'url': 'https://www.techpowerup.com/forums/threads/elmorlabs-pmd2x-features-per-wire-12v-2%C3%976-monitoring-with-overcurrent-alarm.353274/'
    },
    {
        'date': '2026-09-30', 'source': 'TechPowerUp Forums', 'keyword': 'ROG Equalizer',
        'keywords': ['ROG Equalizer', 'Titanload'], 'match': '留言',
        'title': 'Close call... 5090 Burnt Cable — ROG Equalizer 高功耗單機觀察',
        'summary': '使用者收到新的 ROG Equalizer 線材後，裝在 RTX 5090 Lightning Z、1kW BIOS 系統，以約 960～980W 跑分，表示 GPU 端接頭摸起來仍冷，並希望再取得 Titanload 線材做比較。',
        'comments': '使用者同時說原本 Seasonic 隨附線材仍是他的首選，理由是不用額外付費；另一名留言者表示當時在 Amazon 與 AliExpress 都找不到 Titanload。這是單一系統、未提供逐 pin 與溫度數字的短期觀察，不能推成普遍耐受 1kW 或 Equalizer 已完成均流驗證。',
        'url': 'https://www.techpowerup.com/forums/threads/close-call-5090-burnt-cable.334508/post-5799681'
    },
    {
        'date': '2026-09-29', 'source': 'TechPowerUp Forums', 'keyword': 'ThermalProtect',
        'keywords': ['ThermalProtect'], 'match': '留言',
        'title': 'Close call... 5090 Burnt Cable — ThermalProtect 機殼走線個案',
        'summary': '使用者收到白色 ThermalProtect 後，表示線材較軟、在 Torrent Compact 中反而更難避免接頭處碰到側板，也太短而無法從主機板背後走線；他原本希望使用直角轉接器，但不想再增加故障點。',
        'comments': '回覆者認為問題主要是機殼對該顯卡的淨空不足，並指出 ThermalProtect 無法像較硬的原廠線材一樣承受重量、維持彎折路徑。原發文者另設定 HWiNFO 在 12VHPWR 電壓低於 12.00V 時警示，但沒有回報 ThermalProtect 觸發或接頭故障。',
        'url': 'https://www.techpowerup.com/forums/threads/close-call-5090-burnt-cable.334508/post-5799657'
    },
])

# 2026-10-13 weekly refresh：Reddit 與百度貼吧均逐篇展開主文及可見留言；
# TechPowerUp 以 Newer than=2026-10-07、依日期排序搜尋全部產品全名與主要別名，
# 再逐頁閱讀相關樓層。其他論壇以同一日期範圍及在地用語補查，沒有把搜尋摘要
# 或無法讀取全文的結果寫入明細。
reddit_discovery_audit.extend([
    ('ROG Equalizer／WireView／GPU Tweak III Auto-Shutdown', 'https://www.reddit.com/r/ASUSROG/comments/1wzrdwu/after_all_this_time_the_native_12v2x6_cable_is/', '納入', '展開 53 則可見留言；核對原生線不平衡、Equalizer 後續與安裝／購買限制'),
    ('WireView', 'https://www.reddit.com/r/ThermalGrizzly/comments/1wzq1t4/really_need_help_pls/', '納入', '讀取主文及 25 則可見留言；多項交叉讀值支持 WireView 本體量測異常'),
    ('WireView', 'https://www.reddit.com/r/Corsair/comments/1x06ch2/do_i_need_to_replace_my_12vhpwr_cable_on_a_hx1200i/', '納入', '讀取主文及全部可見留言；WireView 找出 pin 5 端子後縮'),
    ('WireView／GPU Safeguard+', 'https://www.reddit.com/r/ThermalGrizzly/comments/1wziij9/gpu_v_psu_protection_properties/', '納入', '讀取主文及 16 則可見留言；確認整段導體監控與 PSU 端接觸不良個案'),
    ('EZDIY-FAB Alpha TS13／GPU Tweak III Auto-Shutdown／WireView／ThermalProtect', 'https://www.reddit.com/r/ASUSROG/comments/1x1oy4s/5090_astral_oc_pin_monitoring/', '納入', '讀取主文及 18 則可見留言；整理溫度監控、逐 pin 差值與軟體關機依賴'),
    ('GPU Safeguard+／WireView／GPU Shield／T-Guard／TempGuard／ThermalProtect', 'https://www.reddit.com/r/buildapc/comments/1x1ny06/4090_undervolting_power_limiting_gadgets_whats/', '納入', '讀取完整主文與 8 則可見留言；只記錄選購認知，未把未附證據的斷言當成產品事實'),
    ('WireView', 'https://www.reddit.com/r/pcmasterrace/comments/1x2amwi/why_12vhpwr_has_not_been_fixed/', '納入', '展開 77 則可見留言；一名使用者以 WireView 找到 PSU 端接點造成的不平衡'),
])
rows.extend([
    {
        'date': '2026-10-12', 'source': 'TechPowerUp Forums', 'keyword': 'WireView',
        'keywords': ['WireView'], 'match': '留言',
        'title': 'DLSS 5 Testing Ends in a Melted RTX 5090 Connector — WireView 驗出第六路 0A',
        'summary': '論壇留言轉貼一件 MSI RTX 5090 Ventus 3X OC 案例：隨卡 12V-2x6 轉接線在使用約 19 個月後發現塑膠熔損；轉貼內容稱線材一直插緊且未曾拔除。這是二手轉貼，不是留言者本人案例。',
        'comments': '轉貼資料稱 WireView Pro II 在總功耗 473.42W 時量到第六路 0.0A，其餘五路為 5.7～8.6A；換成 Corsair 直連線並更換 PSU 插孔後仍有不平衡，顯卡已送保。原始根因尚未確認，因此只能確認轉貼中的量測與送修進度，不能判定是顯卡、線材或接頭哪一端故障。',
        'url': 'https://www.techpowerup.com/forums/threads/dlss-5-testing-ends-in-a-melted-rtx-5090-connector-power-shoots-past-600-w.352412/post-5806810'
    },
    {
        'date': '2026-10-10', 'source': 'Reddit', 'keyword': 'WireView',
        'keywords': ['WireView'], 'match': '留言',
        'title': 'Why 12VHPWR has not been fixed? — WireView 找到 PSU 端不平衡',
        'summary': '主文是一般性的 12VHPWR 設計與責任討論，沒有回報發文者自己的產品故障。',
        'comments': '一名使用者描述 WireView Pro II 曾偵測到電流不平衡；他的 Super Flower Leadex VII 使用 12-pin 轉兩個傳統 8-pin 的 PSU 端接法，追查後發現其中一個 8-pin 位置造成不平衡，改插 PSU 另一個插孔後恢復正常。這是單一系統的檢查結果，沒有提供逐 pin 前後數字。',
        'url': 'https://www.reddit.com/r/pcmasterrace/comments/1x2amwi/why_12vhpwr_has_not_been_fixed/'
    },
    {
        'date': '2026-10-09', 'source': 'Reddit', 'keyword': 'EZDIY-FAB Alpha TS13',
        'keywords': ['EZDIY-FAB Alpha TS13', 'GPU Tweak III Auto-Shutdown', 'WireView', 'ThermalProtect'], 'match': '內文＋留言',
        'title': '5090 Astral OC pin monitoring',
        'summary': 'RTX 5090 Astral OC 使用者在高負載下看到 pin 3～6 的差值略高於 1A，重新插接 GPU 與 PSU 兩端後更新讀值；主文沒有熔損或關機事件。',
        'comments': '一名 Alpha TS13 使用者表示，他已有 Astral 逐 pin 監控與 GPU Tweak III 自動關機，因此主要需要接頭溫度監控；他回報 Alpha TS13 在滿載時各 pin 差值小於 0.4A，但未提供溫度或測試時長。另一名使用者改用 WireView Pro II，理由是擔心作業系統當機時 GPU Tweak III 的軟體關機不會執行；這是架構疑慮，不是已發生失效。另有使用者表示 ThermalProtect 讓單機差值由約 0.5～0.6A 降至約 0.4A。',
        'url': 'https://www.reddit.com/r/ASUSROG/comments/1x1oy4s/5090_astral_oc_pin_monitoring/'
    },
    {
        'date': '2026-10-09', 'source': 'Reddit', 'keyword': 'GPU Safeguard',
        'keywords': ['GPU Safeguard', 'WireView', 'GPU Shield', 'T-Guard', 'TempGuard', 'ThermalProtect'], 'match': '內文＋留言',
        'title': '4090 undervolting, power limiting...? Gadgets? What’s the consensus to minimize a BBQ?',
        'summary': '使用三年的 RTX 4090 使用者尚未遇到熔損，但因擔心風險而比較 WireView Pro II、具保護功能的 PSU，以及 GPU Shield／ThermalProtect 等感測線材；這是選購研究，不是故障案例。',
        'comments': '一名留言者偏好 MSI GPU Safeguard+，理由是可在 Afterburner 設定逐 pin 電流與不平衡門檻，超限後套用降功耗設定或關機，另有 PSU 韌體保護；但留言者沒有提供自己的觸發紀錄。留言中另有未附原始連結的 TempGuard 負面斷言，本報告不把該斷言當成已確認事實。',
        'url': 'https://www.reddit.com/r/buildapc/comments/1x1ny06/4090_undervolting_power_limiting_gadgets_whats/'
    },
    {
        'date': '2026-10-09', 'source': 'TechPowerUp Forums', 'keyword': 'WireView',
        'keywords': ['WireView'], 'match': '內文＋留言',
        'title': 'Close call... 5090 Burnt Cable — 電壓下降、端子變色與 WireView 安裝前後',
        'summary': 'RTX 5090 水冷使用者先發現 16-pin 電壓在約 400W 以下負載時由平常約 11.7V 降至 11.5V；拆下使用約 12 個月的線材後，看到 GPU 端上排外側端子變色。使用者表示該段期間一直降壓、降頻，仍出現早期異常。',
        'comments': '使用者同時換上新 PSU 線材並安裝 WireView Pro II 後，回報負載電壓回到約 11.9V、線材由原先摸起來熱變得較冷，顯示功耗也下降；因線材與 WireView 同時更換，不能把改善單獨歸因於 WireView。後續另反映 WireView 插座卡扣周圍手指空間不足，拔線很困難。',
        'url': 'https://www.techpowerup.com/forums/threads/close-call-5090-burnt-cable.334508/post-5805369'
    },
    {
        'date': '2026-10-09', 'source': 'TechPowerUp Forums', 'keyword': 'ROG Equalizer',
        'keywords': ['ROG Equalizer', 'Titanload'], 'match': '留言',
        'title': 'Close call... 5090 Burnt Cable — Equalizer 與 Titanload 使用者比較',
        'summary': '一名 RTX 5090 Lightning 使用者表示剛取得 ROG Equalizer，但在自己的系統上相較 Seasonic 原廠線材沒有看出差異；他同時稱原廠線材在約 1,100W 跑分負載下未見問題。這是單機短期敘述，沒有逐 pin、溫度或測試時長。',
        'comments': '同一使用者主觀認為 Titanload 比 Equalizer 更好；另一名留言者把 Titanload Pro 描述為「沒有 busbar 的 Equalizer」，並表示當時很難買到。兩者都沒有提供 Titanload 實機對照，不能據此確認結構或效果優劣。',
        'url': 'https://www.techpowerup.com/forums/threads/close-call-5090-burnt-cable.334508/post-5805249'
    },
    {
        'date': '2026-10-08', 'source': 'TechPowerUp Forums', 'keyword': 'ThermalProtect',
        'keywords': ['ThermalProtect'], 'match': '留言',
        'title': 'Close call... 5090 Burnt Cable — ThermalProtect 在 DLSS 5 高負載反覆觸發',
        'summary': '同一名先前回報 ThermalProtect 關機的 RTX 5090 使用者補充：以 4K 執行 DLSS 5 時，若不降低功耗上限，ThermalProtect 會在約 5～10 分鐘內觸發。',
        'comments': '這次補充提供了可重現的時間與條件，但仍沒有觸發溫度、感測端、事件紀錄及關機後接頭檢查。因此可確認的是高負載下反覆中斷，不能確認每次是否都對應實際過熱，也不能判定是否已避免損傷。',
        'url': 'https://www.techpowerup.com/forums/threads/close-call-5090-burnt-cable.334508/post-5804923'
    },
    {
        'date': '2026-10-07', 'source': 'Reddit', 'keyword': 'ROG Equalizer',
        'keywords': ['ROG Equalizer', 'WireView', 'GPU Tweak III Auto-Shutdown'], 'match': '標題＋內文＋留言',
        'title': 'After all this time, the native 12V-2x6 cable is finally showing an uneven current distribution',
        'summary': 'ROG Strix 1200W Platinum 使用者在 OCCT Extreme、GPU 100% 負載時看到原生 12V-2x6 線材電流不平衡；重新插接三次仍相同，但測試本身沒有錯誤。後續檢查發現 PSU 線材接頭內部分端子突出、部分較內縮，因此懷疑線材並訂購 ROG Equalizer。',
        'comments': '另一名同 PSU 使用者表示，WireView Pro II 在僅數月低度使用後對 pin 2、4 發出不平衡警告；換上 Equalizer 後，他回報供電恢復平衡，並分享 WireView 與 GPU Tweak 3 的圖片，但沒有文字列出完整負載數字。其他具體疑慮包括：Lian Li Evo 側板在非直立顯卡配置下無法容納 Equalizer、50% 折扣被運費抵銷、部分地區缺貨／預購；另有留言擔心金鍍層與鍍錫端接的異種金屬腐蝕，但沒有實際腐蝕案例。',
        'url': 'https://www.reddit.com/r/ASUSROG/comments/1wzrdwu/after_all_this_time_the_native_12v2x6_cable_is/'
    },
    {
        'date': '2026-10-07', 'source': 'Reddit', 'keyword': 'WireView',
        'keywords': ['WireView'], 'match': '標題＋內文＋留言',
        'title': 'Really need help pls — WireView Pro II 顯示不合理的 650～700W 閒置功耗',
        'summary': 'Zotac RTX 5090 Solid OC 使用者裝上 WireView Pro II 後立即收到不平衡警告，顯示前四路偏高、第一路約 20A，第二、三路在低於 1A 至 13A 以上劇烈跳動，且桌面閒置功耗顯示約 650～700W。更換 be quiet! 線材、反向接線及更換 PSU 600W 插孔都沒有改善。',
        'comments': 'HWMonitor 與 Nvidia App 同時顯示閒置約 70～80W，GPU 風扇與時脈也符合閒置；多名留言者因此判斷 WireView 本體較可能故障。另一名使用者描述自己曾遇到類似情況，換過多條線與 PSU 都無效，Thermal Grizzly 更換 WireView 後逐 pin 恢復平衡，並肯定客服先寄替換品。這支持先交叉比對讀值及送修裝置，不支持把原警告當成真實 700W 負載。',
        'url': 'https://www.reddit.com/r/ThermalGrizzly/comments/1wzq1t4/really_need_help_pls/'
    },
    {
        'date': '2026-10-07', 'source': 'Reddit', 'keyword': 'WireView',
        'keywords': ['WireView'], 'match': '標題＋內文＋留言',
        'title': 'Do I need to replace my 12VHPWR cable on a HX1200i...',
        'summary': 'HX1200i／RTX 5090 使用者先前收到的 WireView Pro II 風扇到貨即異常，原廠因替換風扇加上關稅成本超過 30 美元而全額退款；之後改買 Noctua Edition。新裝置在 FurMark 下發現 pin 5 約 6～7A、其他 pin 約 9A。',
        'comments': '使用者檢查後發現線材接頭內 pin 5 的方形端子可移動且略微後縮，推回定位後不平衡消失。留言確認 HX1200i／HWiNFO 不提供逐 pin 資料，建議持續觀察 pin 5，若電流再下降就換線。這是 WireView 找到端子問題的正面案例，同時也是一件風扇到貨故障案例。',
        'url': 'https://www.reddit.com/r/Corsair/comments/1x06ch2/do_i_need_to_replace_my_12vhpwr_cable_on_a_hx1200i/'
    },
    {
        'date': '2026-10-07', 'source': 'Reddit', 'keyword': 'WireView',
        'keywords': ['WireView', 'GPU Safeguard'], 'match': '標題＋內文＋留言',
        'title': 'GPU v PSU protection properties?',
        'summary': 'RTX 5090 FE 使用者詢問 WireView 若裝在 GPU 端，能否偵測 PSU 端的不平衡。Thermal Grizzly 代表回覆，逐線電流量測涵蓋 PSU 到 GPU 的整段路徑，除非中間存在跨 pin 的橋接。',
        'comments': '一名使用者提供實際檢查過程：安裝 WireView 後看到不平衡，反覆重插 GPU／WireView 端未改善，最後發現 PSU 端有一個 pin 未正確插入；修正後才理解裝置量到的是整段電路。另有留言說 HWiNFO 可使用 WireView 的逐 pin、差值、溫度與低電壓資料設警報／關機，但程式必須常駐。MSI Ai1300TS／Ai1600TS 被推薦為 PSU 端整合式替代方案，沒有本串觸發實測。',
        'url': 'https://www.reddit.com/r/ThermalGrizzly/comments/1wziij9/gpu_v_psu_protection_properties/'
    },
    {
        'date': '2026-10-05', 'source': '百度貼吧', 'keyword': 'ROG Equalizer',
        'keywords': ['ROG Equalizer', 'Titanload'], 'match': '標題＋內文＋留言',
        'title': '5090烤雞閃紅燈',
        'summary': '百度顯卡吧使用者搭配 ROG Thor 1200W 與 ROG 均流線，遊戲正常但壓力測試會閃紅燈；華碩先前換過新電源後曾正常約一個月，之後問題再出現。10 月 7 日追蹤時，發文者表示已換過兩顆 Thor III 與多條均流線，開始懷疑顯卡接頭並考慮送修。',
        'comments': '留言者從發文者圖片判斷最高與最低 pin 相差近 3A，並建議換線；另有使用者推薦鑫谷強流線，但只說自己已更換，沒有提供前後讀值。也有人以 Seasonic 1600W 原生線表示自己的 5090D 讀值平均，但未提供數字。到 10 月 8 日仍未確認根因或送修結果，因此不能把紅燈直接判定為 Equalizer、PSU 或 GPU 故障。',
        'url': 'https://tieba.baidu.com/p/11079102074'
    },
])

# 補收 2026-10-04 的漏網文章：標題未出現 TempGuard，僅寫 ASRock Taichi 1300W。
# 後續以廠牌＋完整型號＋功能／事故詞交叉查找，不再只依產品名稱。
reddit_discovery_audit.append((
    'TempGuard／GPU Safeguard+／WireView',
    'https://www.reddit.com/r/pcmasterrace/comments/1wwrelq/melted_msi_suprim_rtx_5090_asrock_taichi_1300w/',
    '納入',
    '已讀主文與可見留言；補收 TempGuard 未關機、MSI 保固更換及後續改用 GPU Safeguard+ 的內容',
))
rows.append({
    'date': '2026-10-04', 'source': 'Reddit', 'keyword': 'TempGuard',
    'keywords': ['TempGuard', 'GPU Safeguard', 'WireView'], 'match': '標題＋內文＋留言',
    'title': 'Melted MSI Suprim RTX 5090 - ASRock Taichi 1300W（TempGuard 未關機）',
    'summary': 'MSI RTX 5090 Suprim 使用者表示，顯示卡搭配 ASRock Taichi TC-1300T 與原生 600W 12V-2x6 線材穩定使用約 12 個月；兩端曾確認完全插入、線材沒有急彎，顯示卡長期降壓並設 90% 功耗上限。某次低負載時先失去畫面，接著聞到焦味並看到 GPU 接頭冒煙、產生電弧；GPU 端接頭嚴重熔損，PSU／線材端也受損。發文者表示 ASRock 的溫度感測自動關機功能在冒煙與產生電弧時兩次都沒有關機。這是單一使用者回報，故障起點仍未確認。',
    'comments': 'MSI 因線材兩端都受損而無法判定故障起點，但接受顯示卡保固，約 3.5 週後以整新品更換；ASRock 的電源保固檢查仍在等待。發文者之後改用 MSI Ai1300TS GPU Safeguard+，回報接頭較緊、目前逐 pin 差值約 0.1～0.4A，並把差值警報設為超過 1.0A；尚未發生實際保護觸發。留言有人主張 ASRock 感測器位於接地側而非 12V 側，但本串沒有獨立拆解或量測佐證；其他留言則比較 WireView 與 PSU 內建逐 pin 監控，意見不一。',
    'url': 'https://www.reddit.com/r/pcmasterrace/comments/1wwrelq/melted_msi_suprim_rtx_5090_asrock_taichi_1300w/'
})

# 本次以完整型號、配件料號與功能詞補查；以下 Reddit 討論均已閱讀主文與
# 頁面可見留言。跨版重貼只保留原始討論，不重複計數。
for audit_item in [
    (
        'WireView／GPU Safeguard+',
        'https://www.reddit.com/r/Noctua/comments/1x5w0pt/update_on_my_build_im_adding_a_lil_gpusafety/',
        '納入',
        '已讀主文與可見留言；包含 WireView Pro II Noctua Edition 的選購理由、LCD 待機需求，以及外接監控器與整合式 PSU 的比較',
    ),
    (
        'TempGuard／WireView',
        'https://www.reddit.com/r/ASRock/comments/1wnjh6i/the_ntc_temperature_sensor_on_my_sl1200p_is_next/',
        '納入',
        '已讀主文與可見留言；以 SL-1200P 型號及 NTC sensor 命中，補收直式與 90 度線材的感測器位置拆解',
    ),
    (
        'TempGuard',
        'https://www.reddit.com/r/pcmasterrace/comments/1wp2zp9/pny_denied_my_rtx_5090_warranty_claim_in_writing/',
        '納入',
        '已讀主文與可見留言；以 PG-1600G 型號及熔損／保固詞命中，TempGuard 是否接妥及啟用未獲確認',
    ),
    (
        'TempGuard',
        'https://www.reddit.com/r/ASRock/comments/1wst09n/looking_to_buy_the_lshaped_12vhpwr_cable_for_my/',
        '納入',
        '已讀主文與可見留言；以 SL-1000P、CB-12V2X6L600W 與 90-UCX060-71XCAB 命中線材相容性討論',
    ),
]:
    reddit_discovery_audit.append(audit_item)

# 2026-10-20：以 Chrome 重新查核 Reddit 貼文、內文與可見留言；
# 其中 2026-10-13 的 WireView 討論為前次漏收，本次依 URL 基準標示 New!。
for audit_item in [
    (
        'WireView／GPU Safeguard+',
        'https://www.reddit.com/r/ThermalGrizzly/comments/1x4x9md/wireview_pro_ii_saved_my_5090_potentially_glad_i/',
        '納入',
        '已讀主文與 25 則可見留言；含可重現電流不平衡、PSU 端重插後暫時恢復，以及另一名使用者疑似誤報後改用 Ai1300TS',
    ),
    (
        'WireView',
        'https://www.reddit.com/r/ThermalGrizzly/comments/1x6gv1e/am_i_cooked/',
        '納入',
        '已讀主文與 21 則可見留言；pin 6 讀值歸零與警告在更換線材後消失，原作者確認問題已解決',
    ),
    (
        'WireView／ThermalProtect',
        'https://www.reddit.com/r/PcBuild/comments/1x8gwn7/more_than_2a_imbalance_on_rog_astral_5090/',
        '納入',
        '已讀主文與 21 則可見留言；包含舊線材電流不平衡、WireView 採購考量、ThermalProtect 單機回報與相容性限制',
    ),
    (
        'ThermalProtect',
        'https://www.reddit.com/r/Corsair/comments/1x9mq54/any_update_on_availability_of_the_type4type5/',
        '納入',
        '已讀主文與 3 則可見留言；Type 4／Type 5 版本延後到 10 月仍沒有官方供貨答覆',
    ),
    (
        'WireView／ThermalProtect／Ampinel／GPU Safeguard+／ROG Equalizer',
        'https://www.reddit.com/r/pcmasterrace/comments/1xa9ihs/how_to_avoid_5090_from_burning/',
        '納入',
        '已讀主文並展開 56 則可見留言；只採用實際持有、安裝或更換線材後的回報，推薦與推測分開處理',
    ),
]:
    reddit_discovery_audit.append(audit_item)

rows.extend([
    {
        'date': '2026-10-15', 'source': 'Reddit', 'keyword': 'WireView',
        'keywords': ['WireView', 'GPU Safeguard'], 'match': '標題＋內文＋留言',
        'title': 'Update on my build: I’m adding a lil GPU-safety',
        'summary': '發文者為全 Noctua 主題電腦選購 WireView Pro II Noctua Edition；主因是喜歡 Noctua 版本，並把逐 pin 監控視為額外安全性。主文沒有告警、熔損或關機事件。',
        'comments': '一名已使用約一週的買家希望低負載或待機時可關閉 LCD。支持者重視逐 pin 可視性與 Thermal Grizzly 延長保障；反對者認為外接轉接器會多出兩個接頭，偏好整合監控的 MSI Ai1300TS／Ai1600TS。兩名 MSI 使用者分別表示曾降低門檻測試關機，以及軟體層約 3 秒內動作、PSU 另有硬體門檻；這些是使用者測試／敘述，沒有可匯出的事件紀錄或獨立驗證。',
        'url': 'https://www.reddit.com/r/Noctua/comments/1x5w0pt/update_on_my_build_im_adding_a_lil_gpusafety/'
    },
    {
        'date': '2026-09-29', 'source': 'Reddit', 'keyword': 'TempGuard',
        'keywords': ['TempGuard'], 'match': '標題＋內文＋留言',
        'title': 'ASRock SL-1000P 搭配 L 型 TempGuard 線材的相容性疑問',
        'summary': 'RTX 5080／Steel Legend SL-1000P 使用者因擔心原廠直式線材與機殼側板的淨空，考慮購買 ASRock CB-12V2X6L600W L 型線材；Amazon 頁面只列 Taichi／Phantom Gaming，但 ASRock 官網列出 Steel Legend，造成型號與相容性判讀困難。',
        'comments': '留言一度對感測器小接頭的 pin 數與 SL-1000P 相容性給出互相矛盾的說法；後續有人提供官方線路圖、料號 90-UCX060-71XCAB，並提醒確認 L 型方向與 GPU 接頭方向。發文者尚未回報實際安裝或溫度保護測試，因此本串只能確認購買資訊不一致與方向／接線疑慮，不能確認實機安全效果。',
        'url': 'https://www.reddit.com/r/ASRock/comments/1wst09n/looking_to_buy_the_lshaped_12vhpwr_cable_for_my/'
    },
    {
        'date': '2026-09-24', 'source': 'Reddit', 'keyword': 'TempGuard',
        'keywords': ['TempGuard'], 'match': '內文＋留言',
        'title': 'PNY RTX 5090 搭配 ASRock PG-1600G 原生線材兩端熔損與保固爭議',
        'summary': '發文者表示 PNY RTX 5090 搭配 ASRock PG-1600G ATX 3.1 電源供應器，使用電源隨附的原生 12V-2x6 線材，沒有轉接器或分接器；顯示卡使用原廠 VBIOS、未超頻且功耗上限低於預設。故障發生在閒置時，GPU 與 PSU 兩端都熔損，顯示卡不再被系統偵測。發文者明確表示不知道故障原因，沒有把責任歸給線材。',
        'comments': 'PNY 當日以使用非 PNY 隨附線材為由拒絕保固，未收回硬體檢查；發文者表示公開保固條款與安裝指南沒有這項限制，der8auer 後續提出免費維修。留言雖討論 TempGuard，但主文沒有確認感測器小接頭是否接妥、功能是否啟用或是否曾觸發，所以本報告不把此案例寫成 TempGuard 已確認失效。',
        'url': 'https://www.reddit.com/r/pcmasterrace/comments/1wp2zp9/pny_denied_my_rtx_5090_warranty_claim_in_writing/'
    },
    {
        'date': '2026-09-23', 'source': 'Reddit', 'keyword': 'TempGuard',
        'keywords': ['TempGuard', 'WireView'], 'match': '標題＋內文＋留言',
        'title': 'ASRock SL-1200P 直式與 90 度線材的 NTC 感測器位置拆解',
        'summary': '發文者拆開備用的 SL-1200P 直式 12V-2x6 線材，看到 NTC 感測器貼著 12V 端子、由金屬片固定並包覆在線材內。發文者自行把感測器向接頭方向移近約 0.8 吋，因而不能把改裝後位置當成原廠狀態或保護效果驗證。',
        'comments': '後續更新顯示 ASRock 90 度線材的感測器位於成束 12V／接地線側邊，發文者拆開外殼後認為只接觸一條 12V 線；他擔心原廠約 105°C 門檻與單點接觸可能漏掉其他 pin 的熱點，但沒有實際過熱或關機測試。發文者仍肯定 SL-1200P 的整體價值，並表示自己另用 WireView Pro II 監看；另一名 SL-1000P 使用者則因 Lian Li A3 側板淨空考慮改用 L 型線材。',
        'url': 'https://www.reddit.com/r/ASRock/comments/1wnjh6i/the_ntc_temperature_sensor_on_my_sl1200p_is_next/'
    },
    {
        'date': '2026-02-22', 'source': 'ComputerBase Forum', 'keyword': 'TempGuard',
        'keywords': ['TempGuard', 'WireView', 'Ampinel'], 'match': '標題＋內文＋留言',
        'title': 'ASRock TC-1650T 熱敏感測器只在 GPU 端：使用者補裝 PSU 端感測器',
        'summary': 'Taichi TC-1650T／RTX 4090 使用者指出，兩條原生 12V-2x6 線材的熱敏感測器都靠近 GPU 端，標示約 105°C 關機；他擔心 PSU 端接頭也可能局部過熱，因此詢問第二組感測輸入能否在未接第二條供電線時獨立工作。',
        'comments': '其他留言者找不到 ASRock 對 PSU 端直接溫度感測的明確文件；有人引用拆解，表示 PSU 端 12V-2x6 接頭附近看不到直接感測器，但有過載與過流保護。發文者從備用線材拆出感測器，以 Kapton 膠帶固定在 PSU 端接頭，並用熱風槍確認該改裝會觸發關機；這只能證明他的改裝配置可觸發，不能代表原廠設計或安全建議。發文者認為 WireView／Ampinel 會增加兩個接頭；其他留言者則指出 WireView 的電流監控可在過熱前介入，Ampinel 的主動均流也是不同保護層。',
        'url': 'https://www.computerbase.de/forum/threads/netzteil-mit-heissleiter-am-12v-2x6-stecker-fragen-zum-thermistor.2266294/'
    },
])

rows.extend([
    {
        'date': '2026-10-19', 'source': 'Reddit', 'keyword': 'WireView',
        'keywords': ['WireView', 'ThermalProtect', 'Ampinel', 'GPU Safeguard', 'ROG Equalizer'],
        'match': '內文＋留言',
        'title': 'how to avoid 5090 from burning?',
        'summary': 'RTX 5090 新買家詢問如何降低 12V-2x6 熔損風險，主文只提出 NZXT C1200 Gold ATX 3.1，沒有任何保護產品的實測。',
        'comments': '一名 WireView Pro II 使用者表示裝置曾發現線材電流不平衡與升溫；換成 Corsair ThermalProtect 後，在約 600W 超頻負載下回報電流分布良好、至今未再出現不平衡警告。另一名使用者表示 Ampinel 已裝在 MSI Gaming Trio，但未提供讀值；回覆同時關切安裝淨空與日後拆卸。另有使用者列出 WireView Pro II＋ThermalProtect、ROG Equalizer＋ROG Thor 1200W 的實際配置，但沒有提供保護觸發或前後量測。GPU Safeguard+ 在本串只有推薦與功能認知，沒有實際觸發紀錄。',
        'url': 'https://www.reddit.com/r/pcmasterrace/comments/1xa9ihs/how_to_avoid_5090_from_burning/'
    },
    {
        'date': '2026-10-19', 'source': 'Reddit', 'keyword': 'ThermalProtect',
        'keywords': ['ThermalProtect'], 'match': '標題＋內文＋留言',
        'title': 'Any update on availability of the Type 4／Type 5 ThermalProtect 12V-2x6 cable?',
        'summary': 'HX1000i 使用者表示先前討論預期 Type 4／Type 5 ThermalProtect 約 9 月供貨，但到 10 月仍未上市，因此詢問最新進度。',
        'comments': '頁面只有自動回覆與一則指向 Facebook 貼文的留言，沒有 Corsair 官方答覆、確切上市日或可購買連結。因此本串只證明使用者仍在等待相容版本，不能推定延期原因。',
        'url': 'https://www.reddit.com/r/Corsair/comments/1x9mq54/any_update_on_availability_of_the_type4type5/'
    },
    {
        'date': '2026-10-17', 'source': 'Reddit', 'keyword': 'WireView',
        'keywords': ['WireView', 'ThermalProtect'], 'match': '內文＋留言',
        'title': 'More than 2A imbalance on ROG Astral 5090',
        'summary': 'ROG Astral RTX 5090 使用者以 Corsair RM1200x 2023 與使用約 1.5 年、曾搭配 RTX 4090 的 2×8-pin 轉 12VHPWR 線材，在最高約 540W 時看到最高與最低 pin 差超過 2A；晃動接頭只讓讀值略變，pin 5 仍最低。發文者已購買新的 Corsair Type 5 線材，並考慮加裝 WireView Pro II，但尚未回報更換結果。',
        'comments': '一名 HX1200i Shift／Astral 5090 使用者表示，從電源隨附線換成 ThermalProtect 後，逐 pin 差值明顯縮小，但未提供前後數字。發文者指出自己的 RM1200x 在 PSU 端為 Type 5 2×8-pin，不能使用需要原生 PSU 端 12V-2x6 的 ThermalProtect。其他留言提供重插與接頭受力經驗，但尚未確認本案根因。',
        'url': 'https://www.reddit.com/r/PcBuild/comments/1x8gwn7/more_than_2a_imbalance_on_rog_astral_5090/'
    },
    {
        'date': '2026-10-17', 'source': 'TechPowerUp Forums', 'keyword': 'WireView',
        'keywords': ['WireView', 'ROG Equalizer', 'ThermalProtect'], 'match': '內文＋留言',
        'title': 'WireView Pro II Wired 安裝後出現電壓降、線材升溫與電流不平衡',
        'summary': 'RTX 5090 使用者安裝 WireView Pro II Wired 後，首次回報六路約 7.6～8.4A，但觀察到相較安裝前低於 100mV，電壓降一度增至約 300～400mV，線材也變得很暖；重新插拔後結果反而更差。後續測試曾看到約 170mV 電壓降、pin 6 溫度明顯較高，以及在約 215～350W 時出現不平衡警告。',
        'comments': '發文者明確表示尚不能判定問題來自接入 WireView 的舊線材，或 WireView 內建線材；他已訂購原廠 ASUS 替換線、ROG Equalizer 與 Corsair ThermalProtect 做後續比對。其他留言建議檢查兩端端子與異物，並提醒電壓降可能發生在任一端。到本次查核的最後一則回覆仍未公布換線結果，因此不能把異常直接歸因於 WireView。',
        'url': 'https://www.techpowerup.com/forums/threads/close-call-5090-burnt-cable.334508/post-5809356'
    },
    {
        'date': '2026-10-17', 'source': 'TechPowerUp Forums', 'keyword': 'Ampinel',
        'keywords': ['Ampinel', 'WireView'], 'match': '內文',
        'title': 'WireView Pro 與 Ampinel 在反覆插拔後的單一使用者異常經驗',
        'summary': '一名使用者表示，原版 WireView Pro 在為測試／重新走線而插拔 2～3 次後，遊戲時最高溫由約 65°C 變成持續升到 80°C 以上。',
        'comments': '同一使用者表示 Ampinel 的情況更嚴重：裝置曾觸發警報並關機；第一次安裝時 Aquasuite 顯示電流平衡，但下一次安裝時覺得 12VHPWR 接頭偏鬆。這是單一使用者經驗，沒有拆解、端子量測或原廠判定，不能確認是接頭磨耗、安裝差異或產品本體故障。',
        'url': 'https://www.techpowerup.com/forums/threads/close-call-5090-burnt-cable.334508/post-5809627'
    },
    {
        'date': '2026-10-15', 'source': 'Reddit', 'keyword': 'WireView',
        'keywords': ['WireView'], 'match': '內文＋留言',
        'title': 'Am I cooked',
        'summary': '使用者剛安裝 WireView Pro II Wired 後看到 pin 6 為 0.0A；重插後待機讀值一度正常，但又降回 0.0A，啟動 Cyberpunk 隨即出現 pin 警告。使用者已連接電源按鈕 jumper，但 WireView 沒有自動關機，只能人工關機；接頭沒有焦味或可見燒痕。',
        'comments': '原作者多次回覆確認，更換新的 12VHPWR 線材後警告與讀值異常消失，反覆重插舊線沒有改善，因此本案可標示為已解決，根因指向原線材而非顯示卡。另一名使用者則回報自己遇過相反案例：換線無效、換新 WireView Pro II 才改善；兩者顯示相同症狀可能來自不同位置。原作者認為 WireView 可能及時發現問題，但沒有自動關機仍是明確觀察。',
        'url': 'https://www.reddit.com/r/ThermalGrizzly/comments/1x6gv1e/am_i_cooked/'
    },
    {
        'date': '2026-10-13', 'source': 'Reddit', 'keyword': 'WireView',
        'keywords': ['WireView', 'GPU Safeguard'], 'match': '標題＋內文＋留言',
        'title': 'WireView Pro II saved my 5090 potentially — glad I bought it',
        'summary': '使用者在收到 WireView Pro II 約一週後，執行 RTX 5090 AI 滿載工作時被裝置關機；重新啟動並重跑相同負載後，再次看到電流不平衡。其線材在 PSU 端分成兩個 8-pin，改插不同插孔並重新插妥後暫時恢復，但發文者仍不確定根因。',
        'comments': '另一名使用者安裝 WireView Pro II 後反覆遇到主機板 d6／GPU 未偵測，以及每次重插後不平衡 pin 在 1、3、5 間改變；拆下 WireView 後問題立即消失，因而退貨並改買 MSI MPG Ai1300TS。該使用者後續稱顯示卡無異常、認為此次是誤報，但也承認可能只是個別不良品。另有 Seasonic／RTX 5090 使用者回報自己的 WireView 各 pin 最大差約 0.4A，顯示正反經驗並存。',
        'url': 'https://www.reddit.com/r/ThermalGrizzly/comments/1x4x9md/wireview_pro_ii_saved_my_5090_potentially_glad_i/'
    },
])

# 2026-10-27 更新：逐篇核讀 Reddit 與 TechPowerUp 主文及可見留言後新增／補收。
rows.extend([
    {
        'date': '2026-10-26', 'source': 'Reddit', 'keyword': 'GPU Safeguard',
        'keywords': ['GPU Safeguard', 'WireView', 'ThermalProtect', 'GPU Shield'], 'match': '標題＋內文＋留言',
        'title': 'MSI Safeguard PSU, WireView 2 or Thermal Protect cable?',
        'summary': 'RTX 5090 使用者比較三種方案：價格約 15 英鎊的 ThermalProtect、約 100～150 英鎊的 WireView Pro II，以及約 340 英鎊的 MSI Ai1300TS。主要考量是既有 be quiet! PSU／線材保固、玻璃側板只剩約 3～5 mm 淨空、90 度線材需求，以及第三方線材能否搭配 Safeguard+。',
        'comments': '留言者把 WireView 的相容性、MSI 內建逐 pin 監控可減少外接裝置，以及約 50 美元的 GPU Shield 列為不同取向；其中「任何線材都可搭配 Safeguard+」與保固範圍都只是留言說法，沒有官方文件或實際異常觸發測試。',
        'url': 'https://www.reddit.com/r/buildapc/comments/1xfz1mc/msi_safeguard_psu_wireview_2_or_thermal_protect/'
    },
    {
        'date': '2026-10-26', 'source': 'Reddit', 'keyword': 'WireView',
        'keywords': ['WireView'], 'match': '標題＋內文＋留言',
        'title': 'Is a WireView Pro II Wired Noctua Edition in the works?',
        'summary': 'Founders Edition 顯示卡使用者詢問 WireView Pro II Wired Noctua Edition 的上市時程，希望以直通線形式避開顯示卡端安裝空間限制。',
        'comments': 'Thermal Grizzly 代表回覆原型仍在驗證，量產預估約需 6～7 週；本串沒有產品測試、故障或保護觸發資料。',
        'url': 'https://www.reddit.com/r/ThermalGrizzly/comments/1xfxf7h/is_a_wireview_pro_ii_wired_noctua_edition_in_the/'
    },
    {
        'date': '2026-10-25', 'source': 'Reddit', 'keyword': 'WireView',
        'keywords': ['WireView'], 'match': '標題＋內文＋留言',
        'title': 'WireView Pro II Noctua potential failure',
        'summary': '使用者表示 Noctua Edition 使用約兩週後，在遊戲中出現黑畫面、顯示卡風扇全速及 WireView 顯示 0W；重新開機後仍無畫面，換回已使用約一年的一般版 WireView 即恢復。發文者明確表示接頭與針腳沒有可見熔毀。',
        'comments': '10 月 26 日更新指出 Thermal Grizzly 客服判斷裝置可能故障並寄出替換品。原廠代表表示黑畫面／0W 也可能來自 sense pin 接觸，建議重新插妥並聯絡客服；另一名留言者回報 Noctua 版到貨即因 sense pin 問題無法使用，同樣正在換貨。',
        'url': 'https://www.reddit.com/r/ThermalGrizzly/comments/1xffrjt/wireview_pro_ii_noctua_potential_failure/'
    },
    {
        'date': '2026-10-24', 'source': 'Reddit', 'keyword': 'WireView',
        'keywords': ['WireView'], 'match': '標題＋內文＋留言',
        'title': 'First time using WireView Pro II and current imbalance persists',
        'summary': 'Gigabyte AORUS RTX 5090 使用者首次安裝 WireView Pro II 後看到電流不平衡；更換新的電源線並多次重新插拔後仍持續出現。',
        'comments': '可見留言主要建議重新插妥 PSU、WireView 與 GPU 三端；有人分享自己重插後恢復的經驗，但發文者尚未回報解決結果，因此不能把原因判定為線材、接頭或 WireView 本體。',
        'url': 'https://www.reddit.com/r/ThermalGrizzly/comments/1xe5e28/first_time_using_wireview_pro_2_and_from_that_i/'
    },
    {
        'date': '2026-10-23', 'source': 'Reddit', 'keyword': 'VGA 12+4PIN OCP Dongle',
        'keywords': ['VGA 12+4PIN OCP Dongle', 'GPU Shield', 'WireView'], 'match': '標題＋內文＋留言',
        'title': 'Super Flower to introduce 12V-2x6 overcurrent protection dongle',
        'summary': '主文介紹振華轉接線會監控六路 +12V，任一路 9.5～12A 或任兩路差值超過 6A 且持續 10 秒時警示；單路超過 12A 時進入更高級警報。主文沒有產品實測。',
        'comments': '留言者關心可搭配哪些 PSU／線材；有人誤以為所有 12VHPWR 線材都可通用，隨即有留言提醒模組化 PSU 腳位不同，必須查核相容性。現有 GPU Shield 使用者與多顯示卡實驗室使用者歡迎較低價選項，但沒有實際觸發或長期使用資料。',
        'url': 'https://www.reddit.com/r/pcmasterrace/comments/1xdg04i/superflower_to_introduce_12v2x6_overcurrent/'
    },
    {
        'date': '2026-10-22', 'source': 'TechPowerUp Forums', 'keyword': 'VGA 12+4PIN OCP Dongle',
        'keywords': ['VGA 12+4PIN OCP Dongle', 'GPU Shield', 'ROG Equalizer'], 'match': '標題＋內文＋留言（25 則）',
        'title': "Super Flower's 12V-2x6 OCP Dongle Watches Every Pin, Blacks Out Your Screen on Overcurrent",
        'summary': '主文整理振華逐路電流監控、1,190 元定價、兩級警示與黑畫面保護，並指出首波僅隨 Leadex VIII 電源組合販售；官方尚未說明黑畫面保護的電路實作，也沒有獨立觸發測試。',
        'comments': '多名留言者認為單路超過 12A 後仍等待 180 秒才進入 15 秒倒數過久，且黑畫面容易與驅動程式當機混淆；另有使用者擔心轉接線增加兩個接頭。討論也分成「監控應整合於 PSU」與「逐 pin 量測在 GPU 端串接才較直接」兩派，並提出溫度探頭、事件記錄、保固及獨立販售資訊不足等需求。',
        'url': 'https://www.techpowerup.com/forums/threads/super-flowers-12v-2x6-ocp-dongle-watches-every-pin-blacks-out-your-screen-on-overcurrent.353998/'
    },
    {
        'date': '2026-10-22', 'source': 'Reddit', 'keyword': 'WireView',
        'keywords': ['WireView'], 'match': '標題＋內文＋留言',
        'title': 'PC randomly freezing and restarting after installing WireView',
        'summary': '使用者表示安裝 WireView Pro II 後，電腦會隨機凍結約 10～15 秒再重新啟動；Windows 與 WireView 記錄沒有錯誤，讀值看似正常，且事件曾發生在顯示卡功耗低於 100W 時。',
        'comments': '留言推測可能是未完全插妥或 sense pin 接觸問題，建議重插與檢查接點；發文者尚未回報旁路 WireView 或換貨後的結果，根因未確認。',
        'url': 'https://www.reddit.com/r/ThermalGrizzly/comments/1xcarxf/pc_randomly_freezing_and_restarting_after/'
    },
    {
        'date': '2026-10-21', 'source': 'Reddit', 'keyword': 'WireView',
        'keywords': ['WireView'], 'match': '標題＋內文＋留言',
        'title': 'WireView Pro 2 wire current fluctuates like crazy',
        'summary': 'RTX 5090 使用者在 FurMark 約 600W 時看到單路最高約 9.5A且相對穩定，但遊戲約 500W 時讀值在約 3～12A 間快速變動並觸發警示；發文者把更新／平均間隔設為 50ms。',
        'comments': '留言指出過短取樣間隔會顯示瞬間尖峰，建議改回較長平均值；另一名使用者表示預設 22ms 時六路加總不合理，改為 700ms 後改善。現有內容支持設定影響顯示與警示，但不能證明硬體電流本身異常。',
        'url': 'https://www.reddit.com/r/ThermalGrizzly/comments/1xbu34y/wireview_pro_2_wire_current_fluctuates_like_crazy/'
    },
    {
        'date': '2026-10-21', 'source': 'Reddit', 'keyword': 'WireView',
        'keywords': ['WireView'], 'match': '標題＋內文＋留言',
        'title': 'WireView Pro 2 Wired UK stock',
        'summary': '英國使用者表示 WireView Pro II Wired 已連續 2～3 週難以購買，零售商 Scan 的預估到貨日持續延後，因此考慮一般版加延長線。',
        'comments': 'Thermal Grizzly 代表回覆較大批次即將完成，合作通路約一週後、官方商店隨後補貨；本串沒有故障或保護觸發資料。',
        'url': 'https://www.reddit.com/r/ThermalGrizzly/comments/1xbfso0/wireview_pro_2_wired_uk_stock/'
    },
    {
        'date': '2026-10-17', 'source': 'Reddit', 'keyword': 'WireView',
        'keywords': ['WireView'], 'match': '標題＋內文＋留言',
        'title': 'My WireView Pro II saved me',
        'summary': 'ROG Astral RTX 5090 LC OC 使用者搭配 MODDIY 2×8-pin 轉 12V-2x6 線材，遊戲約三小時後收到 WireView 警報，並看到 pin 6 電流偏低。改回 NVIDIA 原生 4×8-pin 轉接線後，各路電流恢復接近。',
        'comments': '可見留言建議停用原 MODDIY 線材並檢查接頭。發文者認為原線材可能受損，但沒有拆解或量測；文中沒有可見燒痕或熔毀，因此只能確認警報與換線後讀值恢復。',
        'url': 'https://www.reddit.com/r/ThermalGrizzly/comments/1x84ka0/my_wireview_pro_ii_saved_me/'
    },
    {
        'date': '2026-10-12', 'source': 'Reddit', 'keyword': 'WireView',
        'keywords': ['WireView'], 'match': '標題＋內文＋留言',
        'title': 'Graphics driver crashes with WireView',
        'summary': 'AORUS RTX 5090 搭配 WireView Pro II Noctua Edition 後，遊戲約 10～20 分鐘會黑畫面且顯示卡風扇全速；反覆重插、檢查正常讀值與更新韌體都未改善，拆除 WireView 後系統穩定。',
        'comments': 'Thermal Grizzly 寄出替換品後，發文者測試未再當機，因而判定原裝置故障。留言另有相似症狀經重新插妥 PSU 線材後改善的個案，顯示同類症狀仍須逐一比對。本案沒有回報燒痕或熔毀。',
        'url': 'https://www.reddit.com/r/ThermalGrizzly/comments/1x40l9j/graphics_driver_crashes_with_wireview/'
    },
])

reddit_discovery_audit.extend([
    ('本週防護方案比較', 'https://www.reddit.com/r/buildapc/comments/1xfz1mc/msi_safeguard_psu_wireview_2_or_thermal_protect/', '納入', '四種方案的價格、空間、相容性與外接接頭取捨'),
    ('WireView Wired Noctua', 'https://www.reddit.com/r/ThermalGrizzly/comments/1xfxf7h/is_a_wireview_pro_ii_wired_noctua_edition_in_the/', '納入', '原廠代表提供原型驗證與量產時程'),
    ('WireView Noctua', 'https://www.reddit.com/r/ThermalGrizzly/comments/1xffrjt/wireview_pro_ii_noctua_potential_failure/', '納入', '黑畫面／0W、換回舊裝置恢復與客服換貨'),
    ('WireView 不平衡', 'https://www.reddit.com/r/ThermalGrizzly/comments/1xe5e28/first_time_using_wireview_pro_2_and_from_that_i/', '納入', '換線與重插後仍不平衡，原因未確認'),
    ('振華 OCP Dongle', 'https://www.reddit.com/r/pcmasterrace/comments/1xdg04i/superflower_to_introduce_12v2x6_overcurrent/', '納入', '逐路監控、相容性與價格定位留言'),
    ('WireView 凍結重啟', 'https://www.reddit.com/r/ThermalGrizzly/comments/1xcarxf/pc_randomly_freezing_and_restarting_after/', '納入', '安裝後凍結重啟，原因未確認'),
    ('WireView 取樣設定', 'https://www.reddit.com/r/ThermalGrizzly/comments/1xbu34y/wireview_pro_2_wire_current_fluctuates_like_crazy/', '納入', '短取樣造成波動與警示疑慮'),
    ('WireView 英國供貨', 'https://www.reddit.com/r/ThermalGrizzly/comments/1xbfso0/wireview_pro_2_wired_uk_stock/', '納入', '缺貨與原廠補貨時程'),
    ('WireView 線材異常', 'https://www.reddit.com/r/ThermalGrizzly/comments/1x84ka0/my_wireview_pro_ii_saved_me/', '納入', '警報後換線恢復，未見熔毀'),
    ('WireView 裝置故障', 'https://www.reddit.com/r/ThermalGrizzly/comments/1x40l9j/graphics_driver_crashes_with_wireview/', '納入', '替換裝置後黑畫面／風扇全速未再發生'),
])

# 本版指定日期界線；避免歷史基準資料在擴大搜尋時意外越界。
rows = [
    row for row in rows
    if PERIOD_START.isoformat() <= row['date'] <= PERIOD_END.isoformat()
]

report_candidates = [
    path for pattern in (
        '12V2x6_Protection_Forum_Report_*.html',
        '12v2x6_gpu_protection_weekly_report_*.html',
    )
    for path in BASE_DIR.glob(pattern)
]
report_candidates.extend(REPORT_DIR.glob('12v2x6_gpu_protection_weekly_report_*.html'))
report_candidates = [
    path for path in report_candidates
    if path.resolve() != OUT.resolve()
]

def report_file_date(path):
    match = re.search(r'(20\d{2})[-_]?(\d{2})[-_]?(\d{2})', path.name)
    if not match:
        return None
    try:
        return date(int(match.group(1)), int(match.group(2)), int(match.group(3)))
    except ValueError:
        return None

# Same-day corrections must still compare against the previous report date,
# otherwise an earlier draft from today would clear this week's New! badges.
dated_previous_candidates = [
    path for path in report_candidates
    if report_file_date(path) is not None and report_file_date(path) < REPORT_DATE
]
previous_report = (
    max(dated_previous_candidates, key=lambda path: path.stat().st_mtime)
    if dated_previous_candidates else None
)
previous_urls = extract_detail_urls(previous_report) if previous_report else set()

previous_report_label = previous_report.name if previous_report else '無可用前版'
previous_generated_at_label = '無可用前版'
if previous_report:
    try:
        previous_markup = previous_report.read_text(encoding='utf-8')
    except (OSError, UnicodeError):
        previous_markup = ''
    previous_generated_match = re.search(r'產生時間：<b>([^<]+)</b>', previous_markup)
    if previous_generated_match:
        previous_generated_at_label = previous_generated_match.group(1)
previous_report_date_label_match = re.search(r'\d{4}-\d{2}-\d{2}', previous_generated_at_label)
previous_report_date_label = (
    previous_report_date_label_match.group(0)
    if previous_report_date_label_match
    else previous_generated_at_label
)
previous_report_date_match = re.search(r'(\d{4}-\d{2}-\d{2})', previous_report_label)
weekly_focus_start = previous_report_date_match.group(1) if previous_report_date_match else PERIOD_START.isoformat()
weekly_focus_range = f'{weekly_focus_start}～{PERIOD_END.isoformat()}'

# 明細中的問題標籤只從該筆標題、主文摘要與留言摘要的明確文字產生；
# 沒有實際問題描述的功能／規格討論不加標籤，避免把一般風險提醒誤標成故障。
ISSUE_TAG_RULES = [
    ('風扇噪音', r'風扇[^。；，,]{0,50}(?:噪音|異音|摩擦聲)|(?:噪音|異音|摩擦聲)[^。；，,]{0,50}風扇|fan noise|fan.*(?:noisy|noise)'),
    ('風扇故障', r'風扇[^。；，,]{0,50}(?:故障|失效|損壞|自行更換|更換|失效率)|(?:故障|失效|損壞)[^。；，,]{0,50}風扇|fan.*(?:failure|fault|replace)'),
    ('線圈噪音', r'coil whine|線圈聲|線圈噪音'),
    ('接頭熔損', r'熔損|熔化|燒損|burnt cable|burn.*connector|melting'),
    ('接頭高溫', r'(?:接頭|連接器|connector)[^。；，,]{0,22}(?:高溫|過熱|\d+(?:\.\d+)?°C)|(?:高溫|過熱)[^。；，,]{0,22}(?:接頭|連接器|connector)'),
    ('接頭／焊點脫落', r'(?:接頭|連接器|splitter)[^。；，,]{0,24}(?:脫落|斷裂|破裂)|(?:脫落|斷裂|破裂)[^。；，,]{0,24}(?:接頭|連接器|焊點|splitter)|焊點[^。；，,]{0,24}(?:脫落|斷裂)|splitter.*(?:broke|detached)'),
    ('電流不平衡', r'電流不平衡|pin[^。；，,]{0,18}(?:不平衡|差距)|imbalance|current difference'),
    ('軟體／效能問題', r'軟體[^。；，,]{0,24}(?:bug|負載|斷線|效能)|(?:FPS|效能下降|斷線|bug)[^。；，,]{0,24}(?:軟體|WireView|監控)|software.*(?:load|bug|disconnect)'),
    ('安裝／相容性問題', r'無法安裝|安裝[^。；，,]{0,24}(?:問題|困難|不相容)|相容性問題|相容性疑慮|compatibility|空間[^。；，,]{0,18}(?:不足|問題)'),
    ('價格／溢價疑慮', r'(?:價格|價差|溢價)[^。；，,]{0,18}(?:高|貴|過高|過貴)|(?:過貴|價格效益|換機成本)'),
    ('供貨／交期問題', r'交期|缺貨|供貨|上市[^。；，,]{0,18}(?:延後|等待)|shipping delay'),
    ('保固／售後問題', r'拒絕受理保固|保固爭議|拒保|RMA[^。；，,]{0,30}(?:故障|換貨|申請|率|爭議)|安排換貨|聯絡客服[^。；，,]{0,30}(?:更換|故障|問題)|保固[^。；，,]{0,18}(?:拒絕|申請|更換|爭議)'),
]

# 本次逐筆讀取主文與可見留言後的人工覆核結果。
# 已讀不到內容、只看到驗證頁或只有一般規格／風險討論者，刻意留空，避免把推測寫成產品問題。
ISSUE_TAG_OVERRIDES = {canonical_url(url): tags for url, tags in [
    ('https://www.reddit.com/r/pcmasterrace/comments/1xa9ihs/how_to_avoid_5090_from_burning/', ['電流不平衡']),
    ('https://www.reddit.com/r/Corsair/comments/1x9mq54/any_update_on_availability_of_the_type4type5/', ['供貨／交期問題']),
    ('https://www.reddit.com/r/PcBuild/comments/1x8gwn7/more_than_2a_imbalance_on_rog_astral_5090/', ['電流不平衡', '安裝／相容性問題']),
    ('https://www.techpowerup.com/forums/threads/close-call-5090-burnt-cable.334508/post-5809356', ['電流不平衡', '電壓降', '線材升溫', '原因未確認']),
    ('https://www.techpowerup.com/forums/threads/close-call-5090-burnt-cable.334508/post-5809627', ['接頭高溫', '警報／關機', '插拔後異常']),
    ('https://www.reddit.com/r/ThermalGrizzly/comments/1x6gv1e/am_i_cooked/', ['電流不平衡', '自動關機未動作', '線材異常']),
    ('https://www.reddit.com/r/ThermalGrizzly/comments/1x4x9md/wireview_pro_ii_saved_my_5090_potentially_glad_i/', ['電流不平衡', '顯示卡未偵測', '疑似誤報']),
    ('https://www.reddit.com/r/ThermalGrizzly/comments/1wsh3dj/going_from_regular_wv_pro_2_to_noctua_edition/', ['風扇可靠性疑慮']),
    ('https://www.techpowerup.com/forums/threads/thermal-grizzly-and-noctua-introduce-wireview-pro-ii-noctua-edition-gpu-monitoring-device.353137/', ['風扇噪音', '價格／溢價疑慮']),
    ('https://www.chiphell.com/thread-2905450-1-1.html', []),
    ('https://www.hardwareluxx.de/community/threads/thermal-grizzly-lesertest-testet-eine-von-drei-wireview-pro-ii-varianten.1381759/post-31282820', ['接頭／焊點脫落']),
    ('https://www.reddit.com/r/ThermalGrizzly/comments/1wrt3eg/is_there_a_way_to_replace_the_fan/', ['風扇噪音', '風扇故障／更換']),
    ('https://www.reddit.com/r/nvidia/comments/1wp9dx4/rtx_5090_12v2x6_connector_reaches_917c_with_dlss/', ['接頭高溫']),
    ('https://www.reddit.com/r/ThermalGrizzly/comments/1wi53nd/update_post_rog_equalizer_with_wvp_2/', ['電流不平衡']),
    ('https://www.reddit.com/r/ThermalGrizzly/comments/1whd8yh/wireview_pro_2_and_rog_equalizer/', []),
    ('https://www.techpowerup.com/forums/threads/close-call-5090-burnt-cable.334508/post-5794186', ['接頭熔損案例']),
    ('https://www.reddit.com/r/ThermalGrizzly/comments/1wlzsav/gigabyte_rtx_4090_windforce_wireview_pro_2/', ['安裝／相容性問題']),
    ('https://www.techpowerup.com/forums/threads/close-call-5090-burnt-cable.334508/post-5793615', ['接頭熔損風險討論']),
    ('https://extreme.pcgameshardware.de/threads/geforce-rtx-5090-16-pin-stecker-bei-2d-spiel-stark-verschmort.677842/post-12150096', []),
    ('https://www.reddit.com/r/ThermalGrizzly/comments/1wi64cq/wireview_pro_ii_thermals_question/', ['接頭高溫']),
    ('https://www.techpowerup.com/forums/threads/asrocks-tempguard-failed-to-stop-a-psu-side-connector-meltdown-on-a-15-000-rtx-pro-6000-rig.352658/', ['接頭熔損案例', '保護功能失效', '感測位置疑慮']),
    ('https://www.reddit.com/r/ASRock/comments/1wf6dtj/asrock_psu_thermal_protection_fails_to_prevent/', ['接頭熔損案例', '保護功能失效', '感測位置疑慮']),
    ('https://www.reddit.com/r/gpu/comments/1wfcl7m/whats_currently_the_best_option_for_protecting_a/', []),
    ('https://www.techpowerup.com/forums/threads/cooler-master-gpu-shield-adapter-officially-launches-in-the-us.352611/', ['額外接點／故障風險']),
    ('https://extreme.pcgameshardware.de/threads/geforce-rtx-5090-8-pin-stromanschluesse-schlagen-12v-2-6.677683/post-12147632', []),
    ('https://www.techpowerup.com/forums/threads/ezdiy-fab-alpha-ts13.351975/post-5786734', ['量測準確度疑慮', '保護功能限制']),
    ('https://www.techpowerup.com/forums/threads/close-call-5090-burnt-cable.334508/post-5787553', ['接頭熔損風險討論']),
    ('https://www.techpowerup.com/forums/threads/dlss-5-testing-ends-in-a-melted-rtx-5090-connector-power-shoots-past-600-w.352412/post-5786049', ['接頭熔損案例']),
    ('https://www.reddit.com/r/ThermalGrizzly/comments/1w909u4/wireview_pro_2_fan_started_grinding_today/', ['風扇噪音', '風扇故障／更換', '保固／售後問題']),
    ('https://extreme.pcgameshardware.de/threads/dlss-5-schuld-nutzer-berichtet-von-geschmolzenem-stromstecker-seiner-rtx-5090.677607/', []),
    ('https://www.techpowerup.com/forums/threads/hardware-unboxed-falls-victim-to-melted-rtx-5090-power-connector-as-cable-reaches-175%C2%B0c.352273/', ['接頭熔損案例', '接頭高溫', '電流不平衡']),
    ('https://www.reddit.com/r/overclocking/comments/1w4rvzs/cooler_master_gpu_shield_adapter_cable_unboxing/', ['保固／售後限制', '安裝／固定問題']),
    ('https://www.reddit.com/r/ThermalGrizzly/comments/1w2xjye/wireview_pro_ii_worth_for_9070_xt_on_linux/', []),
    ('https://www.reddit.com/r/nvidia/comments/1w0ebt5/cooler_master_gpu_shield_installed_on_a_5090d/', []),
    ('https://www.reddit.com/r/watercooling/comments/1vzqn6s/free_aquacomputer_ampinel_for_reviewer/', ['接頭／製造品質問題']),
    ('https://www.techpowerup.com/forums/threads/close-call-5090-burnt-cable.334508/post-5776023', ['接頭高溫', '接頭熔損風險討論']),
    ('https://www.reddit.com/r/ThermalGrizzly/comments/1vy0wa9/wireview_pro_ii_get_disconnected_by_aida64/', ['軟體／效能問題']),
    ('https://extreme.pcgameshardware.de/threads/high-power-stecker-defekt.677281/', []),
    ('https://www.reddit.com/r/ThermalGrizzly/comments/1vvxc1d/curious_has_there_been_any_melted_cables_with_wvp2/', ['接頭熔損風險討論']),
    ('https://www.techpowerup.com/forums/threads/close-call-5090-burnt-cable.334508/post-5772478', ['接頭高溫']),
    ('https://www.techpowerup.com/forums/threads/close-call-5090-burnt-cable.334508/post-5772336', ['接頭熔損風險討論']),
    ('https://www.reddit.com/r/ThermalGrizzly/comments/1vrjtee/wire_view_pro_2_installed_and_can_now_sleep_a/', ['電流不平衡']),
    ('https://www.reddit.com/r/LinusTechTips/comments/1vqt4vi/regarding_melting_12vhpwr_power_cables_for_nvidia/', ['接頭熔損風險討論']),
    ('https://forums.tomshardware.com/threads/power-supply-and-12vhpwr.3899315/post-23651390', ['接頭熔損案例', '保固／售後問題']),
    ('https://bbs.nga.cn/read.php?tid=47371845', []),
    ('https://bbs.nga.cn/read.php?tid=47361387', []),
    ('https://bbs.nga.cn/read.php?tid=47355461', ['安裝／相容性問題', '保固／售後限制']),
    ('https://bbs.nga.cn/read.php?tid=47354624', ['安裝／相容性問題', '供貨／交期問題']),
    ('https://bbs.nga.cn/read.php?tid=47343776', ['安裝／相容性問題', '價格／溢價疑慮', '額外接點／故障風險', '保固／售後限制']),
    ('https://www.reddit.com/r/ThermalGrizzly/comments/1vebo4v/is_the_thermal_grizzly_wireview_pro_ii_worth/', ['接頭熔損風險討論']),
    ('https://www.reddit.com/r/RTX5080/comments/1vckxvp/rog_equalizer/', ['電流不平衡']),
    ('https://www.techpowerup.com/forums/threads/nvidia-rtx-50-series-gpus-could-see-another-20-30-price-hike-in-2026.351234/post-5762766', []),
    ('https://www.techpowerup.com/forums/threads/close-call-5090-burnt-cable.334508/post-5762386', ['接頭熔損風險討論']),
    ('https://www.reddit.com/r/RTX5080/comments/1vaveb8/new_nvidia_user_scared_of_the_12v2x6_cable/', ['接頭熔損風險討論']),
    ('https://www.techpowerup.com/forums/threads/close-call-5090-burnt-cable.334508/post-5761950', ['接頭熔損風險討論', '保固／售後問題']),
    ('https://www.techpowerup.com/forums/threads/close-call-5090-burnt-cable.334508/post-5760564', ['接頭熔損風險討論', '保固／售後問題']),
    ('https://www.techpowerup.com/forums/threads/close-call-5090-burnt-cable.334508/post-5760028', ['保固／售後限制', '價格／溢價疑慮']),
    ('https://www.reddit.com/r/watercooling/comments/1v5wh2i/ampinel_installed/', ['安裝／相容性問題']),
    ('https://www.reddit.com/r/ThermalGrizzly/comments/1v1r6oc/just_got_the_wireview_pro_ii_and_immediately_got/', ['電流不平衡']),
    ('https://www.reddit.com/r/ThermalGrizzly/comments/1v1jb4z/just_installed_my_new_wireview_pro_ii_wired/', ['安裝／相容性問題']),
    ('https://www.techpowerup.com/forums/threads/close-call-5090-burnt-cable.334508/post-5756316', []),
    ('https://www.reddit.com/r/pcmasterrace/comments/1v120m6/bad_plastic_injection_or_potential_melting/', ['接頭熔損案例', '保固／售後問題']),
    ('https://www.techpowerup.com/forums/threads/close-call-5090-burnt-cable.334508/post-5755006', ['接頭熔損風險討論', '保固／售後問題']),
    ('https://www.reddit.com/r/ThermalGrizzly/comments/1uy826k/wireview_pro_ii_wired_on_rtx_pro_6000_finally_the/', []),
    ('https://www.chiphell.com/thread-2847439-1-1.html', ['安裝／相容性問題']),
    ('https://www.reddit.com/r/ThermalGrizzly/comments/1uxhwl3/wireview_pro_melted_on_my_gigabyte_aorus_rtx_5090/', ['接頭熔損案例', '電流不平衡', '保固／售後問題']),
    ('https://www.techpowerup.com/forums/threads/close-call-5090-burnt-cable.334508/post-5753286', []),
    ('https://www.techpowerup.com/forums/threads/close-call-5090-burnt-cable.334508/post-5752634', ['接頭熔損案例', '保護功能失效', '感測位置疑慮']),
    ('https://www.techpowerup.com/forums/threads/close-call-5090-burnt-cable.334508/post-5752674', ['保護功能限制', '接頭熔損風險討論']),
    ('https://www.reddit.com/r/ASRock/comments/1utcp5x/asrock_tempguard_failed_to_shut_down_system_after/', ['接頭熔損案例', '保護功能失效', '感測位置疑慮']),
    ('https://www.reddit.com/r/pcmasterrace/comments/1ust8i0/avoid_12vhpwr_melting/', ['接頭熔損風險討論']),
    ('https://www.reddit.com/r/MSI_Gaming/comments/1ur8ybe/avoid_msi_ai1600ts_if_you_when_something_silent/', ['線圈噪音', '接頭／焊點脫落']),
    ('https://www.techpowerup.com/forums/threads/msi-mpg-ai1600ts.346215/', ['價格／溢價疑慮', '供貨／交期問題', '軟體／語言限制', '量測準確度疑慮']),
    ('https://www.reddit.com/r/nvidia/comments/1uoepk0/installed_wire_view_pro_ii_and_corsair_thermal/', []),
    ('https://www.reddit.com/r/overclocking/comments/1umu2yx/questions_about_12v2x6_connector_wear_and_cable/', ['電流不平衡']),
    ('https://www.techpowerup.com/forums/threads/close-call-5090-burnt-cable.334508/post-5748182', ['接頭熔損風險討論']),
    ('https://www.reddit.com/r/pcmasterrace/comments/1ulyjce/is_it_werid_that_i_can_afford_an_rtx_5090_but_im/', ['接頭熔損風險討論']),
    ('https://bbs.nga.cn/read.php?tid=47090177', ['電流不平衡', '價格／溢價疑慮', '接頭熔損風險討論']),
    ('https://www.reddit.com/r/ASUSROG/comments/1uktwty/ive_seen_reports_of_the_asus_rog_equalizer_cable/', ['接頭熔損風險討論', '電流不平衡']),
    ('https://www.reddit.com/r/coolermaster/comments/1ukfz35/gpu_shield_availability/', []),
    ('https://www.reddit.com/r/pcmasterrace/comments/1uhce46/wireview_pro_ii_was_worth_it_just_for_the_peace/', []),
    ('https://www.computerbase.de/forum/threads/asus-rog-equalizer-schmorstellen-am-kabel-sind-eine-faelschung.2273324/page-10', []),
    ('https://www.techpowerup.com/forums/threads/close-call-5090-burnt-cable.334508/post-5737373', []),
    ('https://bbs.nga.cn/read.php?tid=46975741', ['接頭熔損案例']),
    ('https://www.techpowerup.com/forums/threads/close-call-5090-burnt-cable.334508/post-5736651', []),
    ('https://www.techpowerup.com/forums/threads/close-call-5090-burnt-cable.334508/post-5736530', []),
    ('https://www.techpowerup.com/forums/threads/thermal-grizzly-shows-new-wireview-pro-ii-noctua-edition-and-new-wireview-ii-at-computex-2026.349824/', []),
    ('https://www.techpowerup.com/forums/threads/cooler-master-launches-mwe-gold-v4-series-with-gpu-shield.349823/', []),
    ('https://www.reddit.com/r/ThermalGrizzly/comments/1tt727g/wireview_pro_ii_w_5090_current_imbalance_limits/', ['電流不平衡']),
    ('https://www.reddit.com/r/MSI_Gaming/comments/1tgsqs4/burned_meg_ai1600t_connector/', []),
    ('https://www.hardwareluxx.de/community/threads/mpg-ai1300ts-pcie5-release.1376483/', []),
    ('https://www.reddit.com/r/ThermalGrizzly/comments/1t32e5j/wireview_pro_2_connection_overheating/', ['電流不平衡', '接頭高溫', '保固／售後問題']),
    ('https://www.reddit.com/r/hardware/comments/1sy32o6/corsair_thermalprotect_review/', []),
    ('https://www.hardwareluxx.de/community/threads/temperatur%C3%BCberwachung-mit-sense-eingriff-das-corsair-thermalprotect-600w-12v-2x6-kabel-ausprobiert.1378713/', []),
    ('https://www.hardwareluxx.de/community/threads/offizieller-nvidia-rtx-5090-overclocking-und-modding-thread.1363289/page-141', []),
    ('https://www.hardwareluxx.de/community/threads/schmelzende-12v-2x6-stecker-asus-rog-equalizer-kabel-h%C3%A4lt-in-extrem-situationen-durch.1378270/', []),
    ('https://www.reddit.com/r/MSI_Gaming/comments/1sgb4pz/msi_ai1600ts_technical_review/', []),
    ('https://extreme.pcgameshardware.de/threads/schmelzende-stromstecker-bei-gpus-msi-will-mit-hardware-alarmsignal-entgegensteuern.673250/', []),
    ('https://www.techpowerup.com/forums/threads/msi-announces-safeguard-for-its-mpg-ai-ts-series-psus.347699/', []),
    ('https://www.reddit.com/r/ThermalGrizzly/comments/1ry7pkp/wireview_pro_ii_thoughts/', []),
    ('https://www.reddit.com/r/ThermalGrizzly/comments/1r6t767/need_exact_cable_recommendation_aorus_p1200w_rtx/', []),
    ('https://www.computerbase.de/forum/threads/wireview-pro-ii-neue-firmware-und-software-mit-vielen-verbesserungen.2265325/', []),
    ('https://www.reddit.com/r/ThermalGrizzly/comments/1qsczjr/wireview_saved_my_4090/', []),
    ('https://www.reddit.com/r/ThermalGrizzly/comments/1qlnurz/pin2_pin6_current_imbalance_summary/', []),
    ('https://www.computerbase.de/forum/threads/thermal-grizzly-wireview-pro-ii-im-test-der-luxus-schutz-fuer-das-12v-2x6-stecker-problem.2263460/page-14', []),
    ('https://bbs.nga.cn/read.php?tid=45988787', ['接頭熔損風險討論', '保固／售後問題']),
    ('https://www.computerbase.de/forum/threads/msi-netzteile-gpu-safeguard-schuetzt-vor-12v-2x6-steckerschaeden.2262806/', ['接頭熔損風險討論']),
    ('https://bbs.nga.cn/read.php?tid=45950741', ['保護功能限制', '保固／售後問題']),
    ('https://www.reddit.com/r/coolermaster/comments/1q6adeu/cooler_master_gpu_shield_ces/', []),
    ('https://www.reddit.com/r/buildapc/comments/1ww7rp7/just_bought_a_5090_how_do_i_prevent_the_melting/', ['接頭熔損風險討論']),
    ('https://www.reddit.com/r/pcmasterrace/comments/1wvgc0k/the_latest_cutscene_in_the_12v2x6_connector/', ['接頭熔損風險討論']),
    ('https://www.reddit.com/r/ThermalGrizzly/comments/1wu2xtp/wireview_pro_2_compatibility/', ['安裝／相容性問題']),
    ('https://www.reddit.com/r/ThermalGrizzly/comments/1wt3sdk/wireview_pro_2_makes_me_crazy/', ['電流不平衡', '告警／量測差異', '自動關機觸發']),
    ('https://www.techpowerup.com/forums/threads/close-call-5090-burnt-cable.334508/post-5803151', ['保護關機觸發']),
    ('https://www.techpowerup.com/forums/threads/elmorlabs-pmd2x-features-per-wire-12v-2%C3%976-monitoring-with-overcurrent-alarm.353274/', []),
    ('https://www.techpowerup.com/forums/threads/close-call-5090-burnt-cable.334508/post-5799681', []),
    ('https://www.techpowerup.com/forums/threads/close-call-5090-burnt-cable.334508/post-5799657', ['安裝／相容性問題']),
    ('https://www.techpowerup.com/forums/threads/dlss-5-testing-ends-in-a-melted-rtx-5090-connector-power-shoots-past-600-w.352412/post-5806810', ['接頭熔損案例', '電流不平衡']),
    ('https://www.reddit.com/r/pcmasterrace/comments/1x2amwi/why_12vhpwr_has_not_been_fixed/', ['電流不平衡']),
    ('https://www.reddit.com/r/ASUSROG/comments/1x1oy4s/5090_astral_oc_pin_monitoring/', ['電流不平衡']),
    ('https://www.reddit.com/r/buildapc/comments/1x1ny06/4090_undervolting_power_limiting_gadgets_whats/', []),
    ('https://www.techpowerup.com/forums/threads/close-call-5090-burnt-cable.334508/post-5805369', ['電壓下降', '端子變色', '接頭高溫', '安裝／拆卸困難']),
    ('https://www.techpowerup.com/forums/threads/close-call-5090-burnt-cable.334508/post-5805249', ['供貨／交期問題']),
    ('https://www.techpowerup.com/forums/threads/close-call-5090-burnt-cable.334508/post-5804923', ['保護關機觸發']),
    ('https://www.reddit.com/r/ASUSROG/comments/1wzrdwu/after_all_this_time_the_native_12v2x6_cable_is/', ['電流不平衡', '端子後縮／突出', '安裝／相容性問題', '供貨／交期問題']),
    ('https://www.reddit.com/r/ThermalGrizzly/comments/1wzq1t4/really_need_help_pls/', ['告警／量測異常']),
    ('https://www.reddit.com/r/Corsair/comments/1x06ch2/do_i_need_to_replace_my_12vhpwr_cable_on_a_hx1200i/', ['風扇故障', '電流不平衡', '端子後縮／鬆動']),
    ('https://www.reddit.com/r/ThermalGrizzly/comments/1wziij9/gpu_v_psu_protection_properties/', ['電流不平衡', '端子未插妥']),
    ('https://tieba.baidu.com/p/11079102074', ['電流不平衡', '告警燈觸發', '保固／送修']),
    ('https://www.reddit.com/r/pcmasterrace/comments/1wwrelq/melted_msi_suprim_rtx_5090_asrock_taichi_1300w/', ['接頭熔損案例', '保護功能失效', '冒煙／電弧', '保固／送修']),
    ('https://www.reddit.com/r/Noctua/comments/1x5w0pt/update_on_my_build_im_adding_a_lil_gpusafety/', ['顯示器無待機關閉', '額外接頭疑慮']),
    ('https://www.reddit.com/r/ASRock/comments/1wst09n/looking_to_buy_the_lshaped_12vhpwr_cable_for_my/', ['相容性疑問', '機殼淨空']),
    ('https://www.reddit.com/r/pcmasterrace/comments/1wp2zp9/pny_denied_my_rtx_5090_warranty_claim_in_writing/', ['接頭熔損案例', '保護狀態未確認', '保固爭議']),
    ('https://www.reddit.com/r/ASRock/comments/1wnjh6i/the_ntc_temperature_sensor_on_my_sl1200p_is_next/', ['感測位置疑慮', '使用者改裝']),
    ('https://www.computerbase.de/forum/threads/netzteil-mit-heissleiter-am-12v-2x6-stecker-fragen-zum-thermistor.2266294/', ['監控範圍疑慮', '使用者改裝']),
    ('https://www.reddit.com/r/ThermalGrizzly/comments/1q2dbfa/wireview_extension_for_fe/', []),
    ('https://www.reddit.com/r/buildapc/comments/1xfz1mc/msi_safeguard_psu_wireview_2_or_thermal_protect/', ['價格／溢價疑慮', '安裝／相容性問題', '額外接點／故障風險']),
    ('https://www.reddit.com/r/ThermalGrizzly/comments/1xfxf7h/is_a_wireview_pro_ii_wired_noctua_edition_in_the/', ['供貨／交期問題']),
    ('https://www.reddit.com/r/ThermalGrizzly/comments/1xffrjt/wireview_pro_ii_noctua_potential_failure/', ['黑畫面／0W', '風扇全速', '疑似裝置故障', '換貨處理中']),
    ('https://www.reddit.com/r/ThermalGrizzly/comments/1xe5e28/first_time_using_wireview_pro_2_and_from_that_i/', ['電流不平衡', '原因未確認']),
    ('https://www.reddit.com/r/pcmasterrace/comments/1xdg04i/superflower_to_introduce_12v2x6_overcurrent/', ['相容性疑問', '額外接點／故障風險', '實測不足']),
    ('https://www.techpowerup.com/forums/threads/super-flowers-12v-2x6-ocp-dongle-watches-every-pin-blacks-out-your-screen-on-overcurrent.353998/', ['警報延遲疑慮', '黑畫面辨識疑慮', '額外接點／故障風險', '供貨／保固資訊不足']),
    ('https://www.reddit.com/r/ThermalGrizzly/comments/1xcarxf/pc_randomly_freezing_and_restarting_after/', ['凍結／重新啟動', '安裝／接觸疑慮', '原因未確認']),
    ('https://www.reddit.com/r/ThermalGrizzly/comments/1xbu34y/wireview_pro_2_wire_current_fluctuates_like_crazy/', ['告警／量測異常', '取樣／平均設定']),
    ('https://www.reddit.com/r/ThermalGrizzly/comments/1xbfso0/wireview_pro_2_wired_uk_stock/', ['供貨／交期問題']),
    ('https://www.reddit.com/r/ThermalGrizzly/comments/1x84ka0/my_wireview_pro_ii_saved_me/', ['電流不平衡', '線材異常', '更換線材後恢復']),
    ('https://www.reddit.com/r/ThermalGrizzly/comments/1x40l9j/graphics_driver_crashes_with_wireview/', ['黑畫面／風扇全速', '裝置故障', '更換裝置後恢復']),
    ('https://www.reddit.com/r/Corsair/comments/1xdndw4/new_rme_psu_with_12v2x6_perpin_overcurrent/', ['型號辨識困難', '價格變動疑慮', '供貨／交期問題', '實測不足']),
    ('https://www.techpowerup.com/forums/threads/corsair-launches-rm1200e-power-supply-with-built-in-pinprotect-gpu-ocp.353971/', ['成本／責任疑慮', '保固／責任疑慮', '實測不足']),
    ('https://www.reddit.com/r/buildapc/comments/1x9km8a/whats_the_latest_on_12v_gpu_connectors/', ['接頭熔損風險討論', '實測不足']),
    ('https://www.computerbase.de/forum/threads/corsair-axi-hxi-und-rme-netzteile-schuetzen-12v-2x6-anschluss.2272561/', ['自動關機／資料損失疑慮', '監控範圍疑慮', '實測不足']),
    ('https://www.hardwareluxx.de/community/threads/thermalprotect-pinprotect-und-pinprotect-corsair-zeigt-schutzl%C3%B6sungen-f%C3%BCr-12v-2x6-problematik.1379683/', ['警示辨識疑慮', '自動關機疑慮', '實測不足']),
]}

def detect_issue_tags(row):
    override_key = canonical_url(row.get('url', ''))
    if override_key in ISSUE_TAG_OVERRIDES:
        return ISSUE_TAG_OVERRIDES[override_key]
    evidence = ' '.join(str(row.get(key, '')) for key in ('title', 'summary', 'comments'))
    return [tag for tag, pattern in ISSUE_TAG_RULES if re.search(pattern, evidence, flags=re.I)]

for row in rows:
    if row['url'] in content_review_overrides:
        row.update(content_review_overrides[row['url']])
    if row['url'] in multi_keyword_map:
        row['keywords'] = multi_keyword_map[row['url']]
    if 'keywords' not in row:
        row['keywords'] = [row['keyword']]
    row.setdefault('keyword', row['keywords'][0])
    row['reviewed'] = True
    row['issue_tags'] = detect_issue_tags(row)
    row['is_new'] = bool(previous_report and canonical_url(row['url']) not in previous_urls)
    if 'match' not in row:
        title_hit = row['keyword'].casefold() in row['title'].casefold()
        row['match'] = '標題＋內文／留言' if title_hit else '內文／留言'
row_urls = {canonical_url(row['url']) for row in rows}
audited_include_urls = {
    canonical_url(url)
    for _, url, status, _ in reddit_discovery_audit
    if status == '納入'
}
missing_audited_urls = audited_include_urls - row_urls
if missing_audited_urls:
    raise RuntimeError(f'Reddit 搜尋覆蓋失敗，已判定納入但明細缺少：{sorted(missing_audited_urls)}')
rows.sort(key=lambda r: r['date'], reverse=True)
new_rows = [row for row in rows if row['is_new']]
counts = {k: sum(k in r['keywords'] for r in rows) for k in kw}
forums = sorted({r['source'] for r in rows})
months = sorted({r['date'][:7] for r in rows}, reverse=True)
keyword_chips = ''.join(f'<button type="button" class="filter-chip" data-value="{escape(k, quote=True)}">{escape(keyword_display_names[k])}</button>' for k in kw)
forum_chips = ''.join(f'<button type="button" class="filter-chip" data-value="{escape(s, quote=True)}">{escape(s)}</button>' for s in forums)
month_chips = ''.join(f'<button type="button" class="filter-chip" data-value="{escape(m, quote=True)}">{escape(m)}</button>' for m in months)
detail = ''.join(
    '<tr data-keyword="{keyword_attr}" data-forum="{source_attr}" data-month="{month_attr}" data-new="{is_new_attr}"><td class="dt">{date}</td><td>{source}</td><td>{keyword_labels}</td>'
    '<td>{match}</td><td class="ti">{new_badge}{title}</td><td class="issue-cell">{issue_labels}</td><td class="sm">{summary}</td><td class="sm">{comments}</td>'
    '<td><a href="{url}" target="_blank" rel="noopener">開啟</a></td></tr>'.format(
        **{k: escape(str(v)) for k, v in r.items() if k != 'url'},
        keyword_attr=escape('|'.join(r['keywords']), quote=True),
        keyword_labels=' '.join(f'<span class="badge">{escape(keyword_display_names.get(k, k))}</span>' for k in r['keywords']),
        issue_labels=' '.join(f'<span class="issue-tag">{escape(tag)}</span>' for tag in r['issue_tags']) or '<span class="issue-none">—</span>',
        is_new_attr='1' if r['is_new'] else '0',
        new_badge='<span class="new-badge">New!</span> ' if r['is_new'] else '',
        source_attr=escape(r['source'], quote=True),
        month_attr=escape(r['date'][:7], quote=True),
        url=escape(r['url'], quote=True)
    ) for r in rows
)
kw_rows = ''.join(
    '<tr><td><span class="badge">{keyword}</span></td><td>{vendor}</td><td>{category}</td><td>{function}</td><td>{aliases}</td><td class="num">{count}</td>'
    '<td><a href="{url}" target="_blank" rel="noopener">{source}</a></td></tr>'.format(
        keyword=escape(keyword_display_names[k]),
        vendor=escape(keyword_vendor[k]),
        category=escape(keyword_category[k]),
        function=escape(keyword_info[k][0]),
        aliases=escape(keyword_search_aliases[k]),
        count=counts[k],
        source=escape(keyword_info[k][1]),
        url=escape(keyword_info[k][2], quote=True)
    ) for k in kw
)

# Section 4 weekly deltas. Every sentence below is tied to the current report's
# New! rows and was added only after the post body and visible comments were read.
pm_weekly_updates = {
    'WireView': {
        'pros': '一名 RTX 4090 使用者以舊 ATX 2.x PSU、四條 8-pin 轉接線及高功耗 BIOS 測得六路最大差約 0.3A、功率差約 4W；另一批留言顯示使用者會用逐 pin 資料確認舊線材狀態及降低心理壓力。這是單機觀察，不代表所有舊 PSU 都同樣穩定。',
        'cons': '新增兩個裝置疑似故障案例：一顆 Normal 版跨兩套系統與多條線材都只顯示 0W、無畫面，官方判斷像是裝置故障；另一顆使用一個多月後出現晃動、不同 pin 變成 0A及 Temp In 超過 80°C，拆除 WireView 後同處探頭滿載最高約 64°C，原廠寄出替換品。另有 FE 使用者擔心延長線形成第三個接點；RTX 5070 討論中，多數留言認為約 200 美元對 250W 顯示卡不划算。',
        'actions': '新增需求：強化出廠通電、夾持力與熱循環檢查；對 0W、晃動、0A及快速升溫提供明確停用／換修判斷。FE／垂直安裝應優先提供少接點的 Wired 方案與完整相容表；選購頁應依 GPU 功耗及是否已有內建逐 pin 監控說明適用族群。',
        'sources': [
            ('0W／無供電案例', 'https://www.reddit.com/r/ThermalGrizzly/comments/1u20yj8/new_wireview_pro_ii_white_normal_defective/'),
            ('晃動與超過 80°C 案例', 'https://www.reddit.com/r/ThermalGrizzly/comments/1t32e5j/wireview_pro_2_connection_overheating/'),
            ('RTX 5070 成本效益討論', 'https://www.reddit.com/r/ThermalGrizzly/comments/1vebo4v/is_the_thermal_grizzly_wireview_pro_ii_worth/'),
        ],
    },
    'GPU Safeguard': {
        'pros': '一名 Safeguard+ 擁有者表示使用感受良好，特別肯定 Afterburner 整合；本週新串未提供新的故障觸發數據，因此只新增這項使用者評價，不延伸成保護效果結論。',
        'cons': '',
        'actions': '',
        'sources': [
            ('Safeguard+ 擁有者回覆', 'https://www.reddit.com/r/Corsair/comments/1v1xadu/corsair_thermal_protect_cable_vs_rog_gpu_power/'),
        ],
    },
    'Ampinel': {
        'pros': '安裝者肯定 Aquasuite 易用；第一顆有後縮 pin 並造成不穩，換貨後晃動與異常消失。另一名留言者表示自己的 Ampinel 與 WireView Pro II 使用超過一個月皆正常，顯示本週案例同時存在正反經驗。',
        'cons': '一名 RTX 5090 Ventus 使用者連續收到兩顆 Rev.4 異常品：第一顆第 2 pin 到貨即後縮；第二顆兩天後第 1 pin 顯示 0A，重載才告警，拆檢見燒痕及另一 pin 後縮、歪斜。原廠說明預設只有總電流達 20A 時，單路 0A 才觸發缺相告警，並表示根因須待退回檢驗。另一篇安裝文顯示剛性外殼會與水冷背板干涉，使用者需切削背板才能完全插妥。',
        'actions': '新增需求：對後縮／歪 pin 增加出廠光學與夾持力檢查，公開 Rev.4／Rev.5 差異與換修判斷；Aquasuite 應明確顯示「0A 但尚未達 20A 告警條件」，並允許低負載缺相先發提示。適配表應納入水冷背板、凹入式接頭與所需淨空。',
        'sources': [
            ('兩顆故障與原廠回覆', 'https://www.reddit.com/r/watercooling/comments/1v9co9h/bad_experience_with_aqua_computer_ampinel_two/'),
            ('安裝、換貨與淨空經驗', 'https://www.reddit.com/r/watercooling/comments/1v5wh2i/ampinel_installed/'),
        ],
    },
    'ROG Equalizer': {
        'pros': '一名 RTX 5090 Astral 使用者快速測試時，Equalizer 在最高約 600W 下沒有 pin 超過 9A，而 Thor III 原線有 pin 超過 9.2A並觸發警報；另有 RTX 5080 Astral 使用者表示一個多月未見異常。這些是少數系統經驗，不能推論普遍效果。',
        'cons': '另一篇比較的兩組逐 pin 數值反算總功率約 668W 與 529W，留言指出並非等負載，因此不能證明 Equalizer 改善完整路徑。留言亦指出 GPU 端 busbar 會讓 Astral 只看到橋接後的分配，無法證明 PSU 到橋接前各線都均衡。另有兩套相同系統使用者表示 CableMod 線的分配比自己的 Equalizer 更平均，顯示結果可能受個體與線材組合影響。',
        'actions': '新增需求：公布相同 GPU、相同功率下，PSU 端、busbar 前與 GPU 端的逐線對照，介面清楚標示監測點；避免把 GPU 端較平均直接表述成全路徑改善。另應提供警報門檻、重插／換線流程及跨 PSU 的實測分布。',
        'sources': [
            ('Equalizer／Thor III 快速比較', 'https://www.reddit.com/r/ASUSROG/comments/1velpgc/rog_equalizer_vs_serie_thor_3/'),
            ('不同總功率與監測點質疑', 'https://www.reddit.com/r/ASUSROG/comments/1v8q6dy/testing_rog_equalizer_recommendation_ignore/'),
            ('CableMod／Equalizer 個人比較', 'https://www.reddit.com/r/cablemod/comments/1vbiwey/i_am_very_happy_with_this_cablemod_12v2x6_cable/'),
        ],
    },
    'ThermalProtect': {
        'pros': '本週留言把 ThermalProtect 視為較便宜、簡單的安全線材選項，也有 TechPowerUp 留言者把它與 Equalizer 一起建議給 RTX 4090 擁有者；但新貼文沒有實際觸發或長期使用證據。',
        'cons': 'RTX 5080 使用者明確擔心：從已通過壓力測試的 Seasonic 原生線換成 ThermalProtect，是否反而增加品質或相容風險。另一篇徵求長期經驗、預警效果與誤報的討論，沒有得到同時長期使用兩種方案的直接比較。',
        'actions': '新增需求：提供依 GPU 功耗、PSU 線材型別與保固條件判斷「維持原生線或改用 ThermalProtect」的決策表；補充長期使用、誤報、觸發前狀態及觸發後處置的可核對案例。',
        'sources': [
            ('RTX 5080 換線風險疑問', 'https://www.reddit.com/r/RTX5080/comments/1vaveb8/new_nvidia_user_scared_of_the_12v2x6_cable/'),
            ('長期經驗與比較需求', 'https://www.reddit.com/r/Corsair/comments/1v1xadu/corsair_thermal_protect_cable_vs_rog_gpu_power/'),
            ('TechPowerUp 安全線材建議', 'https://www.techpowerup.com/forums/threads/nvidia-rtx-50-series-gpus-could-see-another-20-30-price-hike-in-2026.351234/post-5762766'),
        ],
    },
}

# Add the two newly reviewed German forum sources to the current-report deltas.
# These statements are deliberately scoped to the linked post bodies and visible replies.
pm_weekly_updates['WireView']['pros'] += ' Hardwareluxx 一名自年初使用 WireView Pro II 的使用者表示使用正常，並希望推出直通線版以改善空間與外觀。'
pm_weekly_updates['WireView']['cons'] += ' ComputerBase 的可見回覆則提到軟體／韌體 bug、交期與價格，另有使用者認為桌面介面偏技術取向；HWiNFO 整合目前需要 WireView 軟體在背景執行，且有小風扇噪音疑慮。'
pm_weekly_updates['WireView']['actions'] += ' 應提供較輕量且可自訂外觀的本機介面、明確的警報後重插／更換流程，並列出直通線版、正反向版本與機殼淨空相容性。'
pm_weekly_updates['WireView']['sources'].extend([
    ('ComputerBase 軟體、價格與警報疑問', 'https://www.computerbase.de/forum/threads/wireview-pro-ii-neue-firmware-und-software-mit-vielen-verbesserungen.2265325/'),
    ('Hardwareluxx 年初使用與直通線需求', 'https://www.hardwareluxx.de/community/threads/wireview-pro-ii-tg-ver%C3%B6ffentlicht-neue-firmware-und-erste-software-version.1376493/'),
])

pm_weekly_updates['GPU Safeguard']['pros'] += ' Hardwareluxx 的 AI1300TS 擁有者在高功耗測試下回報各 pin 最大差約 0.3A、未聽到線圈聲，屬單機量測；AI1600TS 討論串則把 per-pin 監控視為產品賣點。'
pm_weekly_updates['GPU Safeguard']['cons'] += ' 可見討論同時聚焦高售價與「保護裝置是否處理根因」的疑問，沒有新的實際保護觸發紀錄。'
pm_weekly_updates['GPU Safeguard']['actions'] += ' 應公開可重現的異常電流／接觸不良觸發測試、告警與關機判斷，以及發生後的檢查指引。'
pm_weekly_updates['GPU Safeguard']['sources'].extend([
    ('AI1300TS 擁有者 per-pin 量測', 'https://www.hardwareluxx.de/community/threads/mpg-ai1300ts-pcie5-release.1376483/'),
    ('AI1600TS 保護功能討論', 'https://www.hardwareluxx.de/community/threads/msi-mpg-ai1600ts-im-test-mit-gpu-safeguard-gegen-schmelzende-12v-2x6-stecker.1380494/'),
])

pm_weekly_updates['Ampinel']['cons'] += ' ComputerBase 有買家因新發現的不相容顯示卡而退貨；討論要求更明確的正向相容清單、尺寸與實裝照片。Hardwareluxx 亦有使用者關切主動均流策略與付費更新，原廠回覆該功能可關閉。'
pm_weekly_updates['Ampinel']['actions'] += ' 應公布含水冷背板／凹入式接頭的正向相容表與實測淨空，並在軟體中清楚說明均流策略、預設值、可關閉行為與更新政策。'
pm_weekly_updates['Ampinel']['sources'].extend([
    ('ComputerBase 相容性與退貨討論', 'https://www.computerbase.de/forum/threads/aqua-computer-ampinel-12v-2x6-schutz-ab-16-00-uhr-fuer-100-euro-erhaeltlich.2265345/page-13'),
    ('Hardwareluxx 均流策略與可關閉回覆', 'https://www.hardwareluxx.de/community/threads/%C3%9Cberwachung-und-regelung-des-12v-2x6-wireview-pro-ii-und-ampinel-im-praxisvergleich.1377308/page-2'),
])

pm_weekly_updates['ROG Equalizer']['cons'] += ' ComputerBase 已更新指出流傳的燒焦圖片為偽造；Hardwareluxx 的回覆也質疑斷線測試未必等同高接觸電阻故障。這些討論不能當成實際保護成功或失敗案例。'
pm_weekly_updates['ROG Equalizer']['actions'] += ' 應把媒體測試條件、故障模型與量測點完整公開，並區分斷線、接觸不良與真正過熱，避免未驗證影像左右產品評價。'
pm_weekly_updates['ROG Equalizer']['sources'].extend([
    ('ComputerBase 偽造圖片更正', 'https://www.computerbase.de/forum/threads/asus-rog-equalizer-schmorstellen-am-kabel-sind-eine-faelschung.2273324/page-10'),
    ('Hardwareluxx 故障模型質疑', 'https://www.hardwareluxx.de/community/threads/schmelzende-12v-2x6-stecker-asus-rog-equalizer-kabel-h%C3%A4lt-in-extrem-situationen-durch.1378270/'),
])

pm_weekly_updates['ThermalProtect']['pros'] += ' Hardwareluxx 實測在約 600W、55.4°C 時維持供電，人工加熱至 65°C 後切斷；此為該測試條件下的單一實驗結果。'
pm_weekly_updates['ThermalProtect']['cons'] += ' ComputerBase 與 Hardwareluxx 回覆皆質疑感測器距離接頭、接觸面溫度與延遲；尚無足夠的長期實機誤報資料。'
pm_weekly_updates['ThermalProtect']['actions'] += ' 應公開感測器位置、溫度曲線、切斷閾值／延遲與不同故障注入的重複測試，並提供觸發前提示與事件記錄。'
pm_weekly_updates['ThermalProtect']['sources'].extend([
    ('Hardwareluxx 600W 與人工加熱測試', 'https://www.hardwareluxx.de/community/threads/temperatur%C3%BCberwachung-mit-sense-eingriff-das-corsair-thermalprotect-600w-12v-2x6-kabel-ausprobiert.1378713/'),
    ('ComputerBase 感測位置與機制討論', 'https://www.computerbase.de/forum/threads/corsair-thermalprotect-kabel-zum-schutz-des-12v-2x6-anschlusses.2270488/'),
])

pm_weekly_updates['Titanload'] = {
    'pros': 'Hardwareluxx 一名使用者以同一套系統比較 Titanload 與原生 Seasonic 線，在約 775～800W、30～40 分鐘後以紅外線量得 Titanload 接頭多處約 50～52°C、局部最高約 60～63°C；作者也明確提醒紅外線量測有誤差。',
    'cons': '這是單一系統、短時間與紅外線量測，沒有對照完整的環境、接觸壓力或重複樣本，不能據此判定所有 Titanload 線材的熱表現。',
    'actions': '應提供跨 PSU／GPU、接觸電阻故障注入與校正過的溫度量測；同時公布持續負載時間、量測位置與原生線對照。',
    'sources': [('Hardwareluxx 高功耗紅外線量測', 'https://www.hardwareluxx.de/community/threads/offizieller-nvidia-rtx-5090-overclocking-und-modding-thread.1363289/page-141')],
}

pm_weekly_updates['WireView']['pros'] += ' PCGH Extreme 新增一件近三年未察覺的線材缺接點案例：WireView Pro II 顯示一個 pin 完全無功率，拆查確認沒有金屬接點；450W 顯示卡仍由其餘五條線承載。'
pm_weekly_updates['WireView']['cons'] += ' 這是單一線材個案，不能推算普遍失效率；同時顯示只靠日常使用不一定能察覺單 pin 失效。'
pm_weekly_updates['WireView']['actions'] += ' 應在告警頁提供逐 pin 異常與停用指引，並把裝機前接頭／端子檢查列為明確步驟。'
pm_weekly_updates['WireView']['sources'].append(('PCGH Extreme 缺接點個案', 'https://extreme.pcgameshardware.de/threads/empfehlung-sichtpruefung-defekter-12vhpwr-stecker-hier-betroffen-be-quiet-dark-power-13-1000w.673185/'))
pm_weekly_updates['WireView']['pros'] += ' Hardwareluxx 2025 年討論中，有使用者偏好 WireView Pro 2 的外殼、內建小風扇與顯示器；另一串回覆提到警報後可加第二個溫度感測器監控 PSU 端。'
pm_weekly_updates['WireView']['cons'] += ' 同一討論也明確指出沒有絕對安全方案，故障可能在 GPU／PSU 接頭、兩端線材或線材內部；這不能被摘要成 WireView 已消除所有風險。'
pm_weekly_updates['WireView']['actions'] += ' 應在產品介面中清楚區分 GPU 端與 PSU 端的監控範圍，並說明第二溫度感測器的安裝位置、告警條件與處置限制。'
pm_weekly_updates['WireView']['sources'].extend([
    ('Hardwareluxx WireView Pro 2 Logging 討論', 'https://www.hardwareluxx.de/community/threads/wireview-pro-2-mit-logging-funktion-thermal-grizzly-mit-deltamate-wasserk%C3%BChler-und-der8enchtable.1367906/'),
    ('Hardwareluxx WireView 安全方案討論', 'https://www.hardwareluxx.de/community/threads/12vhpwr-12v-2x6-problematik-boardpartner-mit-bedenken-und-fehlgeschlagenen-l%C3%B6sungsans%C3%A4tzen.1364153/page-9'),
])

pm_weekly_updates['GPU Safeguard']['pros'] += ' PCGH Extreme 使用者認為 GPU Safeguard+ 是有價值的硬體警示功能。'
pm_weekly_updates['GPU Safeguard']['cons'] += ' 具體疑慮是聲音警示是否只會「叫」而不主動關機，以及既有 MSI Ai1300P 使用者必須換整台 PSU 才能取得功能。'
pm_weekly_updates['GPU Safeguard']['actions'] += ' 應公開聲音警示後的確切動作、關機條件與使用者處置；並提供既有 PSU 的升級或外接方案。'
pm_weekly_updates['GPU Safeguard']['sources'].append(('PCGH Extreme 聲音警示討論', 'https://extreme.pcgameshardware.de/threads/schmelzende-stromstecker-bei-gpus-msi-will-mit-hardware-alarmsignal-entgegensteuern.673250/'))

pm_weekly_updates['ROG Equalizer']['pros'] += ' PCGH Extreme 一名 Astral 使用者回報待機 pin 差約 0.02A、負載差約 0.30A，且超頻時沒有達到 9A；這是單一系統讀值。Overclockers UK 另一名使用者則表示換上 ROG Equalizer 後，溫度與各 pin 讀值與約 £10 Corsair 線沒有變化。'
pm_weekly_updates['ROG Equalizer']['cons'] += ' 使用者仍不知道技術上實際改變什麼；升級方案、90 度接頭與狹窄機殼彎折也造成疑問。兩個個案不能證明普遍溫度或均流改善。'
pm_weekly_updates['ROG Equalizer']['actions'] += ' 應公開兩端逐 pin 原始數據、升級流程、接頭方向與機殼淨空；以同一系統的 Corsair／ROG 對照測試說明實際差異。'
pm_weekly_updates['ROG Equalizer']['sources'].extend([
    ('PCGH Extreme pin 差與升級討論', 'https://extreme.pcgameshardware.de/threads/12vhpwr-stecker-asus-rog-equalizer-soll-risiko-senken.673668/'),
    ('Overclockers UK 使用比較', 'https://forums.overclockers.co.uk/threads/corsair-thermalprotect-rog-equalizer-enhanced-12v-2x6-cables.19012784/page-2'),
])

pm_weekly_updates['ThermalProtect']['pros'] += ' PCGH Extreme 留言確認 18 歐元價格與原生 12+4 接口的跨品牌條件；Overclockers UK 討論則把約 £20 價格視為可考慮，但仍等待實測。'
pm_weekly_updates['ThermalProtect']['cons'] += ' 使用者要求 RMx Type 4 與 90 度版本；PCGH Extreme 質疑外部加熱測試是否代表接頭熱點，並指出線材仍未修復接點根因。'
pm_weekly_updates['ThermalProtect']['actions'] += ' 應把 PSU 端型號、原生接口條件、90 度版本與感測器距離列入相容性表，並公布接頭熱點故障注入而非只做外部加熱。'
pm_weekly_updates['ThermalProtect']['sources'].extend([
    ('PCGH Extreme 相容性與感測疑問', 'https://extreme.pcgameshardware.de/threads/12v-2-6-kabel-mit-temperaturschutz-corsair-will-fuer-unter-20-euro-abhilfe-schaffen.674149/'),
    ('Overclockers UK 上市與機構需求', 'https://forums.overclockers.co.uk/threads/corsair-thermalprotect-rog-equalizer-enhanced-12v-2x6-cables.19012784/'),
])

pm_weekly_updates['Ampinel']['pros'] += ' PCGH Extreme Retail 使用者在 MSI RTX 5090 上使用 Type B，回報標準 600W BIOS 超頻運作正常；另一名使用者表示 Type B 尚有約 3–4 mm 背板淨空。'
pm_weekly_updates['Ampinel']['cons'] += ' 同一系列回覆指出 Type A／B、背板淨空、線材調整與硬體監控軟體支援都會影響安裝；另有 PCGH 訂購者因交期與溝通不滿。'
pm_weekly_updates['Ampinel']['actions'] += ' 應提供 Type A／B 方向、背板淨空、線材調整與監控軟體支援的實測清單，並改善交期與訂單狀態溝通。'
pm_weekly_updates['Ampinel']['sources'].append(('PCGH Extreme Retail 安裝與初測', 'https://extreme.pcgameshardware.de/threads/rtx-5090-trifft-auf-aqua-computer-ampinel-retail-version-unboxing-einbau-und-ersteindruck.672373/'))

pm_weekly_updates['ROG Equalizer']['pros'] += ' Chiphell 一名使用者在同時更換 PSU 與 Equalizer 後，回報電壓差由約 0.08–0.14V 降至約 0.04±0.005V，接口溫度也下降。這是前後系統條件不同的個案，只能視為正向使用觀察。'
pm_weekly_updates['ROG Equalizer']['cons'] += ' 因 PSU 與線材同時更換、滿載電壓也改變，不能把改善全部歸因於 Equalizer。NGA玩家社區 另轉述外部測試曾出現約 9.8A／6.2A 的 pin 差，但論壇沒有原始測試條件；貼吧一名使用者遇到 AIDA64／Afterburner 功耗讀值缺失，GPU-Z 正常，根因尚未確認。'
pm_weekly_updates['ROG Equalizer']['actions'] += ' 應以同一 PSU、同一顯卡與固定總功率做換線前後測試，公開逐 pin、接口溫度與重複次數；相容性文件需列出 PSU 世代、IVS、監控軟體與機殼彎折空間，並明確區分強化載流、被動 busbar 與主動均流。'
pm_weekly_updates['ROG Equalizer']['sources'].extend([
    ('Chiphell PSU／Equalizer 更換前後觀察', 'https://www.chiphell.com/thread-2797205-1-1.html'),
    ('NGA玩家社區 17A 與接頭／空間質疑', 'https://bbs.nga.cn/read.php?tid=46564727'),
    ('NGA玩家社區 價格與外部 pin 差轉述', 'https://bbs.nga.cn/read.php?tid=46741152'),
    ('百度貼吧功耗讀值相容性疑問', 'https://tieba.baidu.com/p/10829530764'),
])

pm_weekly_updates['Titanload']['pros'] += ' Chiphell 一名留言者表示自己已購買鑫谷強流線，並把它理解為加粗線材、加長端子的被動式高載流方案；發文者關心能否搭配其他品牌原生 12V-2x6 電源。'
pm_weekly_updates['Titanload']['cons'] += ' 本串沒有逐 pin、溫升或長期測試；留言也指出線材強化不能解決 GPU 端接觸面鬆動。另有不同品牌 16-pin 彎頭線無法插入特定電源的個案，因此不能宣稱所有品牌一定通用。'
pm_weekly_updates['Titanload']['actions'] += ' 應公布可搭配 PSU 型號與接頭公差清單，並用相同系統比較標準線與強流線的接觸電阻、逐 pin 電流、插拔保持力與溫升；產品頁需明確說明它是高載流強化，不是主動均流。'
pm_weekly_updates['Titanload']['sources'].append(('Chiphell 鑫谷強流線相容性與定位討論', 'https://www.chiphell.com/thread-2862733-1-1.html'))

# Keep New! product-evaluation deltas limited to evidence added in this report.
pm_weekly_updates = {
    'ThermalProtect': {
        'pros': 'Dr. Dro 詳細說明它與 ROG Equalizer 的差異並確認相容性：ThermalProtect 為符合規格的標準線材（3-dimple 端子夾持＋溫度斷開 sense pin），售價約 25 美元，可相容任何原生 12VHPWR／12V-2x6 插座，他本人兩者都買了、認為 ThermalProtect 已足夠且較便宜；也在另一起 DLSS 5 當機案例中被推薦為預防性升級選項。',
        'cons': 'Dr. Dro 也提出目前市面上沒有產品能同時滿足他心目中「理想」的安全線材（結合 Equalizer 高承載設計＋ThermalProtect 溫度斷電＋可重置保險絲），意味著 ThermalProtect 目前只做到溫度斷開、不具逐 pin 電流監控或主動均流能力。',
        'actions': '應考慮整合逐 pin 或至少單一電流讀值輸出，讓使用者有早期診斷依據，而不僅是溫度斷電這一種保護層。',
        'sources': [
            ('TechPowerUp ThermalProtect／Equalizer 相容性與規格比較', 'https://www.techpowerup.com/forums/threads/close-call-5090-burnt-cable.334508/post-5793615'),
            ('TechPowerUp 理想安全線材構想', 'https://www.techpowerup.com/forums/threads/close-call-5090-burnt-cable.334508/post-5794186'),
            ('TechPowerUp DLSS 5 當機案例中的預防性推薦', 'https://www.techpowerup.com/forums/threads/dlss-5-cause-gpu-black-screen-and-100-fans-in-every-games-that-i-tried.352696/post-5793196'),
        ],
    },
    'ROG Equalizer': {
        'pros': 'Dr. Dro 說明其相較 ThermalProtect 的優勢：4-spring 端子夾持設計握持力更好、每線可承載更高電流、較不易過熱；同樣在 DLSS 5 當機案例中被推薦為預防性升級選項。',
        'cons': '有留言引用 igorslab.de 評測指出，Equalizer 的端子壁厚度仍是「一般厚度」，端子在插槽內仍可微幅移動，相較 Lian Li 原廠線材採端子直接射出成型、近乎零位移的設計仍有差距；這是留言者依評測圖片與個人觀察的推論，非機構強度測試數據。',
        'actions': '應考慮強化端子周圍塑膠壁的剛性、減少端子在插槽內的可移動空間，向 Lian Li 原生線材的固定方式靠攏。',
        'sources': [
            ('TechPowerUp ThermalProtect／Equalizer 相容性與規格比較', 'https://www.techpowerup.com/forums/threads/close-call-5090-burnt-cable.334508/post-5793615'),
            ('TechPowerUp igorslab 端子壁厚度質疑', 'https://www.techpowerup.com/forums/threads/close-call-5090-burnt-cable.334508/post-5794186'),
        ],
    },
    'WireView': {
        'pros': 'PCGH Extreme 使用者 ParrotHH 確認已依上週計畫為 RTX 5090 FE 加裝 WireView 2 Pro Wired（與 4090 上的 Ampinel 並用），表示兩張卡滿載時「明顯更安心」。',
        'cons': 'PCGH Extreme 一起 PNY RTX 5090 於 2D／低負載情境熔損的案例中，留言者首次提出一個尚未見過的疑慮：即使加裝 WireView 事先偵測到異常、或事後能佐證是接觸不良而非使用者過失，顯卡廠商仍可能反過來主張「問題出在 WireView 本身」而拒絕受理保固；這是留言者個人推測的風險，目前沒有實際案例可佐證。',
        'actions': '應公開加裝 WireView 是否／如何影響原廠保固受理，並取得至少一家主要 GPU／PSU 廠商的明確書面立場，消除使用者對「裝了監控器反而更難主張保固」的疑慮。',
        'sources': [
            ('PCGH Extreme ParrotHH 後續使用心得', 'https://extreme.pcgameshardware.de/threads/geforce-rtx-60-wohl-erst-2028-kopite7kimi-korrigiert-fruehere-prognose.678006/post-12152680'),
            ('PCGH Extreme 2D 熔損案例與保固疑慮', 'https://extreme.pcgameshardware.de/threads/geforce-rtx-5090-16-pin-stecker-bei-2d-spiel-stark-verschmort.677842/post-12150096'),
        ],
    },
    'Ampinel': {
        'pros': 'PCGH Extreme 使用者 ParrotHH 延續上週的採購計畫，確認 4090 持續使用 Ampinel、5090 FE 另外加裝 WireView，兩者並用後表示使用上更安心。',
        'cons': '本週沒有新的量測或故障資料，僅為使用心得延續，不構成新的均流效果證據。',
        'actions': '',
        'sources': [
            ('PCGH Extreme ParrotHH 後續使用心得', 'https://extreme.pcgameshardware.de/threads/geforce-rtx-60-wohl-erst-2028-kopite7kimi-korrigiert-fruehere-prognose.678006/post-12152680'),
        ],
    },
    'EZDIY-FAB Alpha TS13': {
        'pros': '一篇 mini-ITX 改裝完工文確認 Alpha TS13 是整套系統移植進小型化機殼的最後一件零件，已順利裝機（第一次出貨曾遭海關以不明原因退回，第二次下單才到貨）。',
        'cons': '該貼文沒有提供裝機後實際運作中的功耗、溫度讀值或告警紀錄，只確認硬體裝上，不能作為運作效果的證據。',
        'actions': '',
        'sources': [
            ('TechPowerUp mini-ITX 改裝完工文', 'https://www.techpowerup.com/forums/threads/my-mini-itx-project.352847/'),
        ],
    },
}

# Reddit 補查：以下只整理 2026-09-13～2026-09-22 實際讀到的主文與可見留言。
pm_weekly_updates['WireView'] = {
    'pros': 'Reddit 一名 RTX 5080 Astral 使用者在約 370W、室溫 20°C 的 Steel Nomad 測試中，回報 WireView OUT 約 50°C，pin 2–6 約 5.3–5.7A、pin 1 約 3.0–3.3A；另一名水冷使用者在 550–580W、45–60 分鐘負載下讀到 GPU IN 約 70°C、GPU OUT 約 55°C。這些都是單機讀值，不能推論普遍安全門檻。',
    'cons': '留言指出 ROG Equalizer bridge 可能使 WireView 只看到 bridge 到 GPU 的短段，PSU 到 bridge 的個別分配未被同樣監控；也有人認為 WireView 增加第二個接頭，並回報曾有量測線／pin 1 燒損而讀值為 0A。另有高負載水冷案例需要重新插接或增加風流的建議，但沒有共同根因。',
    'actions': '應在介面清楚標示 GPU 端、bridge 後與 PSU 端的實際監控範圍；對 0A、單 pin 失聯、IN 高溫與 bridge 組合提供停用／重插／換修流程，並公布接頭熱點、長時間負載與故障注入的重複測試。',
    'sources': [
        ('ROG Equalizer＋WVP2 pin／溫度讀值', 'https://www.reddit.com/r/ThermalGrizzly/comments/1wi53nd/update_post_rog_equalizer_with_wvp_2/'),
        ('WVP2 水冷高負載溫度問題', 'https://www.reddit.com/r/ThermalGrizzly/comments/1wi64cq/wireview_pro_ii_thermals_question/'),
        ('Equalizer bridge 監控邊界與接頭疑慮', 'https://www.reddit.com/r/ThermalGrizzly/comments/1whd8yh/wireview_pro_2_and_rog_equalizer/'),
    ],
}
pm_weekly_updates['GPU Safeguard'] = {
    'pros': '一名 MSI MPG Ai1300TS 買家表示，選 GPU Safeguard+ 的直接理由是本來就要換 PSU，且不想在機內增加外接監控器與額外接頭；他回報 MSI Center 介面清楚、PSU 可裝入機殼，並分享降壓後 FurMark 約由 575W／60°C 降至 500W／55°C。這是購買理由與單機降壓結果，沒有 Safeguard+ 實際觸發資料。',
    'cons': '同一討論串的其他留言仍在比較外接監控器、GPU Shield、Ampinel 與 ThermalProtect，顯示使用者會權衡水冷背板空間、價格與額外接頭；串內沒有 Safeguard+ 的異常觸發或失效個案。',
    'actions': '應公開整合式 per-pin 監控相較外接裝置的完整監控邊界、觸發門檻、事件記錄與保固處理；同時提供機殼／水冷相容性與「只為 Safeguard+ 更換 PSU」的成本及升級決策資訊。',
    'sources': [
        ('MSI MPG Ai1300TS 買家選購理由與降壓結果', 'https://www.reddit.com/r/watercooling/comments/1wihia6/rtx_5090_owners_worth_upgrading_to_a/'),
    ],
}
pm_weekly_updates['ROG Equalizer'] = {
    'pros': 'RTX 5080 Astral 使用者在 WireView 讀值中看到 pin 2–6 約 5.3–5.7A、pin 1 約 3.0–3.3A，重插後回報差距由約 2.4A 降至約 1.5A；這是同一系統的前後觀察，不是控制測試。',
    'cons': 'Thermal Grizzly 代表明確說明，Equalizer bridge 在 WireView 上游時，WireView 看不到 PSU 到 bridge 的個別分配；留言也質疑把 GPU 端讀值當成全路徑平衡。另有人認為串接 WireView 增加故障點，沒有資料能證明兩者組合已解決所有接頭風險。',
    'actions': '應公開 bridge 前後兩側的逐 pin 量測點、Equalizer＋WireView 的可見與不可見區段，並提供相同 GPU／功率下的前後對照；產品說明需避免讓使用者把局部讀值解讀成 PSU 至 GPU 全路徑的均流結果。',
    'sources': [
        ('RTX 5080 Astral pin 差與重插後讀值', 'https://www.reddit.com/r/ThermalGrizzly/comments/1wi53nd/update_post_rog_equalizer_with_wvp_2/'),
        ('Thermal Grizzly 對 bridge 監控範圍的說明', 'https://www.reddit.com/r/ThermalGrizzly/comments/1whd8yh/wireview_pro_2_and_rog_equalizer/'),
    ],
}
pm_weekly_updates['Ampinel'] = {
    'pros': 'Reddit 使用者在比較 5090 防護方案時，把 Ampinel 列為可考慮的主動均流選項；這是選購討論中的產品認知，沒有本次新增的 Ampinel 實機量測或觸發紀錄。',
    'cons': '同一討論串的主要疑慮是水冷背板空間、價格及是否值得為了防護更換整個 PSU；留言沒有提供 Ampinel 的前後對照或故障率資料。',
    'actions': '應以實機清單補充水冷背板與機殼淨空、價格／保固及主動均流的可驗證測試，避免只在多產品選購討論中以「主動均流」作為未經實測的優勢。',
    'sources': [
        ('5090 防護方案比較', 'https://www.reddit.com/r/watercooling/comments/1wihia6/rtx_5090_owners_worth_upgrading_to_a/'),
    ],
}
pm_weekly_updates['ThermalProtect'] = {
    'pros': 'Reddit 使用者將 ThermalProtect 列為 5090 的外接選項之一，與 WireView、Ampinel 及整合式 PSU 一起比較；本次沒有讀到它的新增實機觸發或長期使用數據。',
    'cons': '選購討論顯示使用者仍擔心水冷背板空間、額外接頭及是否值得改裝；沒有留言能證明 ThermalProtect 在該串中已改善實際接頭風險。',
    'actions': '應提供水冷／背板相容性、額外接頭影響、觸發前後行為與長期誤報資料，並用相同系統與外接監控、整合式 PSU 做可核對比較。',
    'sources': [
        ('5090 防護方案比較', 'https://www.reddit.com/r/watercooling/comments/1wihia6/rtx_5090_owners_worth_upgrading_to_a/'),
    ],
}
pm_weekly_updates['GPU Shield'] = {
    'pros': 'Reddit 留言把 GPU Shield 列為可考慮的替代方案之一，但本次沒有讀到 GPU Shield 的實際安裝、觸發或長期使用資料。',
    'cons': '同一串留言對 GPU Shield 是否實際有用存在分歧，沒有共同測試或故障案例可判斷其保護效果。',
    'actions': '應公開獨立的接觸不良／過熱故障注入測試、動態降功率與警報門檻，並與 WireView、Ampinel、ThermalProtect 在接頭數量及可見監控範圍上做同條件比較。',
    'sources': [
        ('GPU Shield 選購爭論', 'https://www.reddit.com/r/watercooling/comments/1wihia6/rtx_5090_owners_worth_upgrading_to_a/'),
    ],
}
# 本次產生報告只放 2026-10-07～2026-10-13 的新評價；前版 New! 內容由
# previous_report 動態讀回，避免把前一週內容重複標成本次新增。
pm_weekly_updates = {
    'WireView': {
        'pros': 'Reddit 有兩件可追到實際接點的案例：一件找出 HX1200i 線材 pin 5 端子略微後縮，推回後不平衡消失；另一件找出 PSU 端有 pin 未插妥。另有 Super Flower 使用者把不平衡追到 PSU 端其中一個 8-pin 插孔，改插另一位置後恢復。TechPowerUp 一名 RTX 5090 使用者在發現舊線端子變色後，同時換新線並裝上 WireView，回報負載電壓由約 11.5V 回到 11.9V、線材由摸起來熱變得較冷；因兩項變更同時進行，改善不能單獨歸因於 WireView。',
        'cons': '一台 WireView Pro II 在閒置桌面顯示約 650～700W、單路約 20A，但 HWMonitor／Nvidia App 只有約 70～80W；換線、換插孔仍相同，留言依交叉讀值判斷裝置本體較可能故障。另一名買家第一台 WireView 風扇到貨即異常，最後由原廠退款。TechPowerUp 使用者也反映插座卡扣周圍空間不足，拔線很困難。',
        'actions': '裝置應在開機自檢中比對總功耗、六路加總與 GPU 回報值，遇到數百瓦差異時明確顯示「量測裝置可能故障」而不是只報 pin 不平衡；同時保存原始取樣與告警紀錄供客服判讀。硬體面需加入風扇轉速／堵轉自檢，並增加卡扣操作空間或附安全拆卸工具。',
        'sources': [
            ('端子後縮與風扇到貨故障', 'https://www.reddit.com/r/Corsair/comments/1x06ch2/do_i_need_to_replace_my_12vhpwr_cable_on_a_hx1200i/'),
            ('不合理的閒置功耗讀值', 'https://www.reddit.com/r/ThermalGrizzly/comments/1wzq1t4/really_need_help_pls/'),
            ('PSU 端 pin 未插妥', 'https://www.reddit.com/r/ThermalGrizzly/comments/1wziij9/gpu_v_psu_protection_properties/'),
            ('舊線變色與換線／安裝 WireView 後觀察', 'https://www.techpowerup.com/forums/threads/close-call-5090-burnt-cable.334508/post-5805369'),
        ],
    },
    'GPU Safeguard': {
        'pros': 'Reddit 留言者選擇 MSI GPU Safeguard+ 的理由，是可在 Afterburner 設逐 pin 電流與不平衡門檻，超限後套用低功耗設定或關機，另有 PSU 韌體層斷電；其他討論也把 Ai1300TS／Ai1600TS 視為不需外接監控器的整合式替代方案。這些是功能認知與選購理由。',
        'cons': '本週沒有讀到 GPU Safeguard+ 實際偵測異常、降載或斷電的事件紀錄，也沒有相同故障下軟體層與韌體層先後動作的資料；因此不能從推薦留言判定兩層保護均已驗證。',
        'actions': '應提供可匯出的事件時間線，分別列出每一 pin 讀值、軟體降載／關機與 PSU 韌體斷電的門檻及先後順序；並公開在 Afterburner 未啟動、當機或 USB 通訊中斷時，韌體層仍可獨立完成的保護範圍。',
        'sources': [
            ('4090 防護產品選購討論', 'https://www.reddit.com/r/buildapc/comments/1x1ny06/4090_undervolting_power_limiting_gadgets_whats/'),
            ('WireView 與整合式 PSU 比較', 'https://www.reddit.com/r/ThermalGrizzly/comments/1wziij9/gpu_v_psu_protection_properties/'),
        ],
    },
    'ROG Equalizer': {
        'pros': 'Reddit 一名同樣使用 ROG Strix 1200W 的使用者，在原生線僅使用數月後收到 WireView pin 2、4 不平衡警告；換上 Equalizer 後，他回報供電恢復平衡並分享 WireView／GPU Tweak 3 圖片。另一名 ThermalProtect 使用者則回報自己的逐 pin 差值縮小。這些都是單機觀察，沒有相同負載的完整文字數據。',
        'cons': '同一 Reddit 串出現三項具體使用障礙：Lian Li Evo 側板在非直立顯卡配置下無法容納線材、50% 折扣因運費而只省約 10 美元、部分地區只能預購且約等兩週。百度使用者搭配 Thor 1200W／均流線仍在壓力測試閃紅燈，換過兩顆 Thor III 與多條線後問題再發，根因尚未確認。TechPowerUp 另有使用者表示 Equalizer 相較 Seasonic 原生線沒有看出差異。',
        'actions': '應在相容表加入機殼側板距離、顯卡方向與最小彎曲空間，並把折扣後含運價與各區交期透明化。針對紅燈／近 3A 差值案例，需提供可匯出的逐 pin 紀錄與依序換線、換 PSU、送修 GPU 的判定流程，避免使用者反覆更換整套硬體仍無法定位。',
        'sources': [
            ('原生線不平衡與 Equalizer 後續', 'https://www.reddit.com/r/ASUSROG/comments/1wzrdwu/after_all_this_time_the_native_12v2x6_cable_is/'),
            ('百度均流線壓力測試紅燈', 'https://tieba.baidu.com/p/11079102074'),
            ('Equalizer 與 Seasonic 原生線比較', 'https://www.techpowerup.com/forums/threads/close-call-5090-burnt-cable.334508/post-5805249'),
        ],
    },
    'ThermalProtect': {
        'pros': 'TechPowerUp 同一名 RTX 5090 使用者補充，4K 執行 DLSS 5 時若不降低功耗上限，ThermalProtect 會在約 5～10 分鐘內反覆觸發，提供了比上週更具體的重現條件。Reddit 另有單機回報逐 pin 差值由約 0.5～0.6A 縮小到約 0.4A，但這不是控制測試。',
        'cons': '5～10 分鐘觸發紀錄仍沒有溫度、感測端、事件檔及關機後接頭檢查，無法分辨每次是必要保護或過度敏感；高負載遊戲會被中斷，使用者必須降低功耗上限才能持續運作。',
        'actions': '線材應保存每次觸發時的兩端溫度、功耗、持續時間與感測器狀態，讓使用者能區分真實過熱與誤觸發；同時提供「先降載、持續升溫再斷電」的可選策略及清楚的安全界線。',
        'sources': [
            ('DLSS 5 高負載反覆觸發', 'https://www.techpowerup.com/forums/threads/close-call-5090-burnt-cable.334508/post-5804923'),
            ('Astral 使用者的逐 pin 差值觀察', 'https://www.reddit.com/r/ASUSROG/comments/1x1oy4s/5090_astral_oc_pin_monitoring/'),
        ],
    },
    'GPU Tweak III Auto-Shutdown': {
        'pros': 'RTX 5090 Astral 使用者把 GPU Tweak III 自動關機視為既有的逐 pin 過流保護，因此另購 Alpha TS13 時主要補足接頭溫度監控；這反映軟體功能能與溫度顯示裝置分工，但沒有本週觸發紀錄。',
        'cons': '另一名使用者停用 GPU Tweak III 自動關機並改用 WireView Pro II，理由是擔心作業系統凍結時軟體關機無法執行。這是架構層面的合理疑慮，不是已觀察到的失效案例。',
        'actions': '應在介面明確說明服務未啟動、作業系統當機與驅動失聯時的保護狀態，並提供不依賴 Windows 的硬體備援或與 PSU／主機板韌體聯動。',
        'sources': [
            ('Astral pin 監控與關機方案比較', 'https://www.reddit.com/r/ASUSROG/comments/1x1oy4s/5090_astral_oc_pin_monitoring/'),
        ],
    },
    'EZDIY-FAB Alpha TS13': {
        'pros': '一名 RTX 5090 Astral 使用者表示，Alpha TS13 正好補足他需要的接頭溫度監控，使用上「符合需求」；他另回報滿載時逐 pin 差值小於 0.4A。這是單一裝機觀察，沒有溫度值、測試時長或告警事件。',
        'cons': '本週資料只支持顯示／監控用途，沒有證明 Alpha TS13 能主動關機或避免熔損；使用者仍依賴 Astral 內建逐 pin 監控與 GPU Tweak III 自動關機。',
        'actions': '產品頁與螢幕應明確區分「顯示／警報」和「主動切斷」能力；報告最高溫度、感測器位置、記錄期間與告警是否需要人工處置，避免把低差值誤解為裝置主動均流。',
        'sources': [
            ('Alpha TS13 溫度監控使用心得', 'https://www.reddit.com/r/ASUSROG/comments/1x1oy4s/5090_astral_oc_pin_monitoring/'),
        ],
    },
    'Titanload': {
        'pros': 'TechPowerUp 一名使用者主觀推薦 Titanload，另一名留言者把 Titanload Pro 描述為沒有 busbar 的 Equalizer；本週沒有任何 Titanload 實機數據，因此這些只算產品認知。',
        'cons': '留言者表示 Titanload Pro 當時很難買到；百度也有人推薦鑫谷強流線，但只說自己已更換，沒有換線前後逐 pin、溫度或觸發資料。',
        'actions': '應改善可購得性，並公開線材結構、端子規格與固定負載下的逐 pin／溫度對照；中國市場的「強流線」宣傳也需附可重現測試，不能只靠名稱暗示均流或安全效果。',
        'sources': [
            ('Titanload 與 Equalizer 比較', 'https://www.techpowerup.com/forums/threads/close-call-5090-burnt-cable.334508/post-5805249'),
            ('百度均流線案例中的強流線推薦', 'https://tieba.baidu.com/p/11079102074'),
        ],
    },
}

# 2026-10-27 本次新增／補收的評價；前版卡片由 previous_report 讀回。
pm_weekly_updates = {
    'WireView': {
        'pros': '補收兩件有處置結果的案例。10 月 17 日案例在 pin 6 電流偏低並警報後，改回 NVIDIA 原生轉接線即恢復正常；10 月 12 日黑畫面／風扇全速案例更換 WireView 本體後未再發生，可確認原裝置故障。兩案都沒有回報可見熔毀。',
        'cons': '10 月 25 日 Noctua Edition 使用約兩週後發生黑畫面、風扇全速與 0W，換回舊 WireView 即恢復，客服判斷可能故障並換貨；另有一顆到貨即有 sense pin 問題。其他新串還包括安裝後隨機凍結／重啟、換線與反覆重插仍不平衡，以及 50ms 短取樣造成 3～12A 快速波動與警示。這些案例未出現熔毀，但顯示裝置故障、接觸與取樣設定可能產生相似症狀。',
        'actions': 'P0：針對黑畫面、0W、風扇全速與 sense pin 接觸加入開機自檢，並在顯示器與事件記錄區分「裝置故障」「接觸異常」「真實過流」。P1：出廠增加 sense pin、熱循環與負載測試，公開批次／RMA 處理資訊。P1：為更新／平均間隔提供安全預設與說明，避免把瞬間尖峰當成持續性異常；診斷流程應要求依序旁路裝置、換線與重插三端。',
        'sources': [
            ('換線後電流恢復', 'https://www.reddit.com/r/ThermalGrizzly/comments/1x84ka0/my_wireview_pro_ii_saved_me/'),
            ('替換 WireView 後黑畫面消失', 'https://www.reddit.com/r/ThermalGrizzly/comments/1x40l9j/graphics_driver_crashes_with_wireview/'),
            ('Noctua Edition 疑似故障與換貨', 'https://www.reddit.com/r/ThermalGrizzly/comments/1xffrjt/wireview_pro_ii_noctua_potential_failure/'),
            ('安裝後凍結與重啟', 'https://www.reddit.com/r/ThermalGrizzly/comments/1xcarxf/pc_randomly_freezing_and_restarting_after/'),
            ('取樣／平均設定影響讀值', 'https://www.reddit.com/r/ThermalGrizzly/comments/1xbu34y/wireview_pro_2_wire_current_fluctuates_like_crazy/'),
        ],
    },
    'GPU Safeguard': {
        'pros': 'RTX 5090 使用者在新一輪選購比較中重視把逐 pin 監控與保護整合於 PSU，理由是少用一個外接轉接器；這是明確購買考量，不是保護觸發實測。',
        'cons': '約 340 英鎊價格明顯高於外接方案；使用者也找不到原生 90 度線材，並不確定第三方線材是否影響 Safeguard+ 功能或保固。留言雖稱任何線材都能使用，但沒有官方相容性文件支持。',
        'actions': 'P1：提供原生 90 度線材及完整的官方線材／保固相容表，明確區分監控功能可用、建議搭配與保固承認三種狀態。P2：把逐 pin 監控下放到較低瓦數／價格產品，並提供真實接觸不良下的警示、降載與硬體保護時間線。',
        'sources': [
            ('Safeguard、WireView 與 ThermalProtect 選購比較', 'https://www.reddit.com/r/buildapc/comments/1xfz1mc/msi_safeguard_psu_wireview_2_or_thermal_protect/'),
        ],
    },
    'ThermalProtect': {
        'pros': '同一選購比較把 ThermalProtect 的約 15 英鎊低價視為最大優點，適合只需要接頭過熱保護、且電源端具原生 12V-2x6 的使用者；本串沒有實際觸發紀錄。',
        'cons': '發文者擔心搭配 be quiet! PSU 是否影響保固，也因沒有 90 度版本而難以在側板淨空有限的機殼使用。留言未能提供可核對的跨品牌保固答案。',
        'actions': 'P1：公布跨品牌 PSU 使用條件、保固邊界與完整接頭需求，並推出 90 度／低高度版本。產品頁應把溫度保護與逐 pin 電流監控的差異放在同一張比較表，避免低價被誤解為功能完全相同。',
        'sources': [
            ('Safeguard、WireView 與 ThermalProtect 選購比較', 'https://www.reddit.com/r/buildapc/comments/1xfz1mc/msi_safeguard_psu_wireview_2_or_thermal_protect/'),
        ],
    },
    'GPU Shield': {
        'pros': '新選購串中，有留言者把約 50 美元的 GPU Shield 列為比 WireView 便宜的第四種方案；振華討論串也有現有 GPU Shield 使用者歡迎更多同類選擇。這只反映價格定位與產品認知。',
        'cons': '本次沒有 GPU Shield 的實際告警、降功率或長期使用資料；留言所稱的功能也沒有在該串中驗證。',
        'actions': 'P1：用可公開重現的逐 pin 異常測試呈現警告、降功率與處置結果，並把價格、線材長度、額外接頭及保固與其他外接方案並列。',
        'sources': [
            ('四種防護方案選購比較', 'https://www.reddit.com/r/buildapc/comments/1xfz1mc/msi_safeguard_psu_wireview_2_or_thermal_protect/'),
            ('振華 OCP Dongle 討論中的 GPU Shield 使用者', 'https://www.reddit.com/r/pcmasterrace/comments/1xdg04i/superflower_to_introduce_12v2x6_overcurrent/'),
        ],
    },
    'VGA 12+4PIN OCP Dongle': {
        'pros': '官方已明列六路 +12V 電流門檻、路間差值警示、ARGB／蜂鳴器與黑畫面保護流程；1,190 元價格低於多數帶螢幕逐 pin 監控器。Reddit 的多顯示卡實驗室使用者認為較低成本有吸引力，現有 GPU Shield 使用者也歡迎多一種選擇。',
        'cons': 'TechPowerUp 留言集中質疑單路超過 12A 後仍等待 180 秒才進入 15 秒倒數、黑畫面容易與驅動程式當機混淆，以及轉接線會增加兩個接頭。首波僅與 Leadex VIII 電源組合販售，獨立販售、相容線材及保固資訊不足；目前也沒有擁有者的實際觸發或長期資料。',
        'actions': 'P0：公開黑畫面保護如何介入、是否中止 GPU 取電、裝置失效時的安全行為，並縮短或允許設定高電流等待時間。P1：加入非揮發事件記錄與明確故障代碼，公布相容 PSU／線材、獨立販售與保固條件。P1：以單路高阻抗、過流、路間失衡及接頭局部加熱做第三方重複測試，並評估增加溫度感測。',
        'sources': [
            ('Super Flower OCP Dongle TechPowerUp 完整討論', 'https://www.techpowerup.com/forums/threads/super-flowers-12v-2x6-ocp-dongle-watches-every-pin-blacks-out-your-screen-on-overcurrent.353998/'),
            ('Super Flower OCP Dongle Reddit 討論', 'https://www.reddit.com/r/pcmasterrace/comments/1xdg04i/superflower_to_introduce_12v2x6_overcurrent/'),
        ],
    },
    'PinProtect／PinProtect+': {
        'pros': '本次新發表的第二代 RM1200e 讓買家直接因 PinProtect 逐 pin OCP 下單；其他 Reddit 留言者也把 PSU 內建監控視為高功耗 GPU 的較完整方案，具體理由是不用像 WireView／Ampinel 類外接裝置再增加兩個 12V-2x6 接頭。ComputerBase 亦有留言肯定 PinProtect+ 可透過 iCUE 讀取六路電流。這些是購買理由與功能評價，不是保護觸發實測。',
        'cons': 'Reddit 買家無法只靠 RM1200e 名稱分辨 2023、2025 舊代與第二代 PinProtect 版，且遇到官網價格由 204.99 美元變為 279.99 美元、延至 11 月出貨；CORSAIR 人員需以 CP-9020316／CP-9020317 料號協助辨識。TechPowerUp、ComputerBase 與 Hardwareluxx 留言另擔心為接頭問題額外付費、PSU 端監控看不到 GPU 接頭局部溫度、紅色 LED 在封閉機殼內不易看見，以及切斷 GPU 可能造成遊戲中斷或未儲存資料遺失。目前沒有擁有者觸發、熔毀或長期使用資料。',
        'actions': 'P0：在產品名稱、包裝與通路頁統一標示 PinProtect 世代、CP 料號與支援功能，並避免同名舊代混售。P1：公開逐 pin 門檻、量測精度、反應時間、異常恢復邏輯及接觸不良故障注入測試；清楚說明它只偵測電流、不直接量測接頭溫度。P1：在 GPU 切斷前加入可辨識的蜂鳴警示與可匯出事件記錄，並說明 iCUE 未執行時的硬體保護、保固與資料保存行為。',
        'sources': [
            ('RM1200e 第二代料號、價格與供貨討論', 'https://www.reddit.com/r/Corsair/comments/1xdndw4/new_rme_psu_with_12v2x6_perpin_overcurrent/'),
            ('RM1200e PinProtect TechPowerUp 完整討論', 'https://www.techpowerup.com/forums/threads/corsair-launches-rm1200e-power-supply-with-built-in-pinprotect-gpu-ocp.353971/'),
            ('ComputerBase 兩頁完整討論', 'https://www.computerbase.de/forum/threads/corsair-axi-hxi-und-rme-netzteile-schuetzen-12v-2x6-anschluss.2272561/'),
            ('Hardwareluxx 警示方式討論', 'https://www.hardwareluxx.de/community/threads/thermalprotect-pinprotect-und-pinprotect-corsair-zeigt-schutzl%C3%B6sungen-f%C3%BCr-12v-2x6-problematik.1379683/'),
            ('內建 PSU 與外接監控器比較', 'https://www.reddit.com/r/buildapc/comments/1x9km8a/whats_the_latest_on_12v_gpu_connectors/'),
        ],
    },
}

def pm_points(value):
    points = [point.strip() for point in re.split(r'(?<=[。！？])\s*|；', value or '') if point.strip()]
    if not points:
        return '<p class="pm-empty">目前沒有足夠的使用者內容可整理。</p>'
    return '<ul class="pm-list">{}</ul>'.format(''.join(f'<li>{escape(point)}</li>' for point in points))

def pm_delta(value):
    if not value:
        return ''
    return '<div class="pm-new"><div class="pm-new-title"><span class="new-badge">New!</span><b>本次新增</b> <span class="pm-new-date">({escape_range})</span></div>{points}</div>'.format(
        escape_range=escape(weekly_focus_range), points=pm_points(value)
    )

def pm_weekly_sources(items):
    if not items:
        return ''
    links = '、'.join(
        f'<a href="{escape(url, quote=True)}" target="_blank" rel="noopener">{escape(label)}</a>'
        for label, url in items
    )
    return f'<div class="pm-new-source"><span class="new-badge">New!</span><b>本次依據（{escape(weekly_focus_range)}）：</b>{links}</div>'

def extract_previous_new_parts(markup):
    """Read the previous report's marked New! blocks by product and aspect."""
    section_match = re.search(r'<section id="reviews">(.*?)<div class="tabs">', markup, re.S)
    section_markup = section_match.group(1) if section_match else markup
    cards = {}
    for card_match in re.finditer(r'<article class="pm-product">(.*?)</article>', section_markup, re.S):
        card = card_match.group(1)
        heading_match = re.search(r'<h3>(.*?)</h3>', card, re.S)
        if not heading_match:
            continue
        product = re.sub(r'<[^>]+>', '', heading_match.group(1)).replace('New!', '').strip()
        parts = {}
        for class_name, key in (
            ('pm-positive', 'pros'),
            ('pm-negative', 'cons'),
            ('pm-action', 'actions'),
        ):
            aspect_match = re.search(
                rf'<section class="pm-aspect {class_name}">(.*?)</section>', card, re.S
            )
            if aspect_match:
                aspect = aspect_match.group(1)
                start = aspect.find('<div class="pm-new">')
                parts[key] = aspect[start:] if start >= 0 else ''
        source_match = re.search(r'<footer class="pm-evidence">.*?(<div class="pm-new-source">.*?</div>)</footer>', card, re.S)
        parts['sources'] = source_match.group(1) if source_match else ''
        if any(parts.values()):
            cards[product] = parts
    return cards

previous_evaluation_parts = {}
comparison_report = previous_report
if comparison_report and comparison_report.exists():
    previous_evaluation_parts = extract_previous_new_parts(
        comparison_report.read_text(encoding='utf-8')
    )

def previous_new_content(fragment):
    if not fragment:
        return ''
    return fragment.replace(
        '<b>本週更新</b>',
        '<b>前版內容（報告日期：2026-09-23）</b>'
    ).replace(
        '本週依據（2026-09-17～2026-09-23）',
        '前版依據（報告日期：2026-09-23）'
    )

def extract_new_items(fragment):
    if not fragment:
        return []
    class LeafListParser(HTMLParser):
        def __init__(self):
            super().__init__()
            self.stack = []
            self.items = []

        def handle_starttag(self, tag, attrs):
            if tag == 'li':
                if self.stack:
                    self.stack[-1]['has_child_li'] = True
                self.stack.append({'parts': [], 'has_child_li': False})

        def handle_endtag(self, tag):
            if tag == 'li' and self.stack:
                item = self.stack.pop()
                if not item['has_child_li']:
                    text = ''.join(item['parts']).strip()
                    text = re.sub(r'^前版內容：\s*', '', text)
                    if text:
                        self.items.append(text)

        def handle_data(self, data):
            if self.stack:
                self.stack[-1]['parts'].append(data)

    parser = LeafListParser()
    parser.feed(fragment)
    return parser.items

def merged_new_content(old_fragment, current_fragment):
    old_items = extract_new_items(old_fragment)
    current_items = extract_new_items(current_fragment)
    if not old_items and not current_items:
        return ''
    groups = []
    if old_items:
        groups.append(
            '<div class="pm-history-group"><b>前版內容（報告日期：{0}）：</b>'
            '<ul class="pm-list">{1}</ul></div>'.format(
                escape(previous_report_date_label),
                ''.join(f'<li>{item}</li>' for item in old_items)
            )
        )
    if current_items:
        groups.append(
            '<div class="pm-history-group"><b><span class="new-badge">New!</span>本次新增（{0}）：</b>'
            '<ul class="pm-list">{1}</ul></div>'.format(
                escape(weekly_focus_range),
                ''.join(f'<li>{item}</li>' for item in current_items)
            )
        )
    return '<div class="pm-new"><div class="pm-new-title"><b>前版內容與本次新增</b></div>{}</div>'.format(
        ''.join(groups)
    )

def merged_new_sources(old_fragment, current_fragment):
    old_links = re.findall(r'<a\s[^>]*>.*?</a>', old_fragment or '', re.S)
    current_links = re.findall(r'<a\s[^>]*>.*?</a>', current_fragment or '', re.S)
    if not old_links and not current_links:
        return ''
    parts = []
    if old_links:
        parts.append(
            '<span><b>前版依據（報告日期：{0}）：</b>{1}</span>'.format(
                escape(previous_report_date_label), '、'.join(old_links)
            )
        )
    if current_links:
        parts.append(
            '<span><b><span class="new-badge">New!</span>本次依據（{0}）：</b>{1}</span>'.format(
                escape(weekly_focus_range), '、'.join(current_links)
            )
        )
    return '<div class="pm-new-source">{}</div>'.format('<br>'.join(parts))

pm_cards = ''.join(
    '<article class="pm-product"><div class="pm-product-head"><div><span class="pm-kicker">產品評價</span><h3>{keyword} {row_new}</h3></div>'
    '<span class="evidence">{strength}</span></div><div class="pm-aspects">'
    '<section class="pm-aspect pm-positive"><h4>優點／使用價值</h4>{pros}{merged_pros}</section>'
    '<section class="pm-aspect pm-negative"><h4>缺點／使用疑慮</h4>{cons}{merged_cons}</section>'
    '<section class="pm-aspect pm-action"><h4>改善方向</h4>{actions}{merged_actions}</section></div>'
    '<footer class="pm-evidence"><a href="{url}" target="_blank" rel="noopener">查看既有依據</a>{merged_sources}</footer></article>'.format(
        keyword=escape(product_display_names[k]),
        row_new='<span class="new-badge">New!</span>' if k in pm_weekly_updates else '',
        pros=pm_points(pm_info[k][0]),
        cons=pm_points(pm_info[k][1]),
        actions=pm_points(pm_info[k][2]),
        strength=escape(pm_info[k][3]),
        url=escape(pm_info[k][4], quote=True),
        merged_pros=merged_new_content(
            previous_evaluation_parts.get(product_display_names[k], {}).get('pros', ''),
            pm_delta(pm_weekly_updates.get(k, {}).get('pros', ''))
        ),
        merged_cons=merged_new_content(
            previous_evaluation_parts.get(product_display_names[k], {}).get('cons', ''),
            pm_delta(pm_weekly_updates.get(k, {}).get('cons', ''))
        ),
        merged_actions=merged_new_content(
            previous_evaluation_parts.get(product_display_names[k], {}).get('actions', ''),
            pm_delta(pm_weekly_updates.get(k, {}).get('actions', ''))
        ),
        merged_sources=merged_new_sources(
            previous_evaluation_parts.get(product_display_names[k], {}).get('sources', ''),
            pm_weekly_sources(pm_weekly_updates.get(k, {}).get('sources', []))
        ),
    ) for k in kw
)

generated_at_label = f"{GENERATED_AT.strftime('%Y-%m-%d %H:%M:%S')} Asia/Taipei"
REPORT_VERSION = 'v1.6'
V12_UPDATED_AT = '2026-08-19 14:45:56 Asia/Taipei'

# 只讓本次才新增的追蹤產品顯示 New!；版本號依使用者要求暫不變更。
new_keywords = {'VGA 12+4PIN OCP Dongle', 'PinProtect／PinProtect+'}

# 版本紀錄（架構變動：新增論壇／關鍵字／版型調整）與內容更新紀錄（每次查核跑了什麼、
# 找到什麼）分成兩份清單呈現，避免版本號被日常內容更新灌水，也讓兩種資訊各自好找。
version_history = [
    ('v1.6', '2026-09-09', '新增 EZDIY-FAB Alpha TS13 為第 12 個追蹤關鍵字——U 型 12V-2x6 直通轉接器，內建 TFT 螢幕在不需軟體下顯示 GPU 功耗與接頭溫度，85°C 觸發警報（TechPowerUp 站方 W1zzard 親自評測發現）。「五、搜尋結果明細」改為預設只顯示前 10 筆（依目前篩選條件），點擊「顯示更多」再逐次多顯示 10 筆，避免長表格一次全部展開。'),
    ('v1.5', '2026-09-02', '新增 ASUS GPU Tweak III Auto-Shutdown 為第 11 個追蹤關鍵字（僅追蹤其過流自動關機功能本身），順序排在 ROG Equalizer 旁邊（同為 ASUS 產品）；新增 PCGH Extreme 站內搜尋來源（先前因 Cloudflare 驗證頁未查核，已確認正確搜尋路徑 /search/）；「五、搜尋結果明細」新增月份篩選。自本版起，日常內容更新不再逐次遞增版本號，只在架構變動（新增論壇、新增關鍵字、版型調整）時才進版；本版之前的 v1.2～v1.3 仍沿用舊制，其中部分屬於現在會歸類為「內容更新」的項目。'),
    ('v1.3', '2026-08-26', 'Revision History 新增版本時間記錄，並更正 v1.2 的更新時間為上週報告時間。'),
    ('v1.2', V12_UPDATED_AT, '新增 Hardwareluxx、ComputerBase、PCGH Extreme 與 Overclockers UK 四個論壇來源。'),
]
update_log = [
    ('2026-10-27', '新增 CORSAIR PinProtect／PinProtect+ 為第 14 個追蹤產品；依官方資料確認兩者皆整合於 PSU、只偵測六路 +12V 電流，不直接量測溫度。PinProtect 固定常駐且預設異常持續 30 秒後使 GPU 停止取電；PinProtect+ 另有 iCUE 即時讀值、通知、記錄與可調門檻／10～180 秒延遲。版本依使用者規則維持 v1.6，待確認後再進版。'),
    ('2026-10-27', 'PinProtect 專項搜尋：逐篇核讀 Reddit 第二代 RM1200e 料號／價格／供貨討論、TechPowerUp RM1200e PinProtect 發表串與 8 則回覆、ComputerBase 兩頁 32 則留言、Hardwareluxx 完整討論，以及既有 Reddit／Chiphell 比較串。新增 4 篇唯一明細並重分類 4 篇既有明細；沒有擁有者實際觸發、燒毀或熔毀案例。'),
    ('2026-10-27', '新增 Super Flower（振華）VGA 12+4PIN 過電流保護轉接線／OCP Dongle 為第 13 個追蹤產品；依官方頁確認它是 Adapter 線材、只偵測六路 +12V 電流，不宣稱溫度監控。逐篇核讀 TechPowerUp 25 則貼文／留言及 Reddit 討論，整理門檻、180 秒等待、黑畫面辨識、額外兩個接頭、相容性、供貨與保固疑慮；官方未公開黑畫面保護電路，不寫成已確認切斷 GPU 電源。'),
    ('2026-10-27', 'Reddit：以產品全名、品牌／型號、逐 pin 電流、黑畫面、熔毀與供貨等情境詞補查並逐篇核讀，新增／補收 10 篇唯一討論。WireView 包含兩件裝置更換或換線後可追到結果的案例，以及 Noctua Edition 疑似故障、凍結重啟、持續不平衡、取樣設定與 Wired 版交期；新資料沒有確認的燒毀或熔毀案例。'),
    ('2026-10-27', 'TechPowerUp：登入狀態正常，完成自動驗證後，以 2026-10-20 之後日期查核既有追蹤產品及主要別名；新增振華 OCP Dongle 完整討論。PinProtect 專項再以產品名、RM1200e／HX1000i SHIFT CRYSTAL、per-pin OCP 與在地用語回溯搜尋 2025-07-01 之後資料，找到 Reddit、TechPowerUp、ComputerBase、Hardwareluxx 與 Chiphell 可用內容；Tom’s Hardware、Overclockers UK、PCGH Extreme、NGA玩家社區與百度貼吧未找到可新增且已完整核讀的唯一討論，搜尋空白不解讀為沒有討論。'),
    ('2026-10-20', 'Reddit：以 Chrome 重新查核產品全名、完整型號、12V-2x6 事故詞及留言分頁，逐篇閱讀主文並展開可見回覆；新增／補收 5 篇唯一討論。重點包括 WireView 找出線材異常後換線解決、疑似誤報後改用 Ai1300TS、ROG Astral 超過 2A 不平衡、ThermalProtect Type 4／Type 5 供貨詢問，以及 5090 防護產品的實際使用回報。推薦、功能描述與實際觸發分開記錄。'),
    ('2026-10-20', 'TechPowerUp：登入狀態正常，以 Newer than=2026-10-15、依日期排序查核全部 12 個追蹤關鍵字及 Ai1300TS／Equalizer 等別名；新增 WireView Pro II Wired 安裝後電壓降、線材升溫與電流不平衡的待確認案例，以及同串另一名使用者的 WireView／Ampinel 反覆插拔後異常經驗。換線結果尚未公布，不把原因歸給特定產品。'),
    ('2026-10-20', 'Tom’s Hardware、ComputerBase、Hardwareluxx、Overclockers UK、PCGH Extreme、Chiphell、NGA玩家社區與百度貼吧：補查 2026-10-15 後產品名、完整型號及中德英在地用語的公開可讀結果；未找到可新增且已完整核讀主文與留言的唯一討論，搜尋空白不解讀為沒有討論。'),
    ('2026-10-15', 'Reddit：以產品名之外的完整 PSU／線材型號、配件料號、NTC／thermistor 與熔損情境詞補查，逐篇閱讀主文與可見留言；新增 10/15 WireView Pro II Noctua Edition 選購／使用討論，並補收先前漏掉的 SL-1200P 感測器拆解、PG-1600G 原生線材兩端熔損與保固爭議、SL-1000P 搭配 CB-12V2X6L600W 的相容性討論，以及 TC-1300T TempGuard 未關機熔損個案。跨版重貼排除。'),
    ('2026-10-15', 'ComputerBase：加入 Heißleiter／Thermistor 等德文功能詞與完整型號補查，逐樓核讀 TC-1650T 討論；新增原廠只在 GPU 端配置線材感測器的疑慮、使用者自行把備用感測器改裝到 PSU 端並以熱風槍確認關機，以及對 WireView／Ampinel 額外兩個接頭的正反意見。大型 17 頁討論串只找到單一購買理由留言，因未完成整串逐頁核讀，不納入明細。'),
    ('2026-10-15', 'TechPowerUp：完成 Chrome 驗證後，以 Newer than=2026-10-13 查找 WireView、TempGuard、Ai1300TS、ThermalProtect、Equalizer 與 12V-2x6。只找到 WireView 泛用推薦、RX 9070 XT 接頭討論及既有長串延伸留言，沒有足以新增為獨立產品實測的內容。Tom’s Hardware、Hardwareluxx、Overclockers UK、PCGH Extreme、Chiphell、NGA玩家社區與百度貼吧亦補查 10/13 後公開可讀結果，未找到可新增且已完整核讀的唯一討論。'),
    ('2026-10-13', 'Reddit：以產品全名、品牌型號與 12V-2x6 情境詞補查 2026-10-07 之後的貼文及留言，逐篇展開核讀 7 筆唯一討論；新增 WireView 量測裝置疑似故障、端子後縮／PSU 端未插妥、ROG Equalizer 換線後單機回報、Alpha TS13 溫度監控、GPU Tweak III 軟體依賴，以及 GPU Safeguard+ 選購理由。未把留言中未附原始證據的產品斷言寫成事實。'),
    ('2026-10-13', 'TechPowerUp：登入狀態正常，未出現驗證頁；用 Newer than=2026-10-07、依日期排序查核全部 12 個追蹤關鍵字及主要別名，逐頁閱讀相關樓層。新增 WireView 驗出熔損轉接線第六路 0A 的二手案例、舊線端子變色後換線並安裝 WireView 的前後觀察、ThermalProtect 在 4K DLSS 5 下約 5～10 分鐘反覆觸發，以及 Equalizer／Titanload 的使用者比較。'),
    ('2026-10-13', '百度貼吧：以均流線、強流線、逐 pin／單針電流與 16-pin 燒接口等在地用語補查，逐樓核讀顯卡吧「5090烤雞閃紅燈」及 10 月 8 日前可見留言，新增 ROG 均流線搭配 Thor 電源仍反覆告警、換過兩顆電源與多條線後根因未定的個案。Tom’s Hardware、ComputerBase、Hardwareluxx、Overclockers UK、PCGH Extreme、Chiphell、NGA玩家社區以 2026-10-07 之後日期與中德英在地用語補查；本輪未找到可新增且可完整核讀主文與留言的唯一討論。'),
    ('2026-10-07', 'Reddit：以產品全名、品牌型號與 12V-2x6 情境詞補查 2026-09-29 之後的結果，逐篇核讀 4 筆唯一討論及可見留言；新增 WireView 反覆不平衡／自動關機與 GPU Tweak 3 讀值差異、Gainward RTX 5080 相容性、5090 FE 防護方案比較，以及換線是否能根治熔損的討論。'),
    ('2026-10-07', 'TechPowerUp：完成驗證後，以 Newer than=2026-09-29、依日期排序查核全部產品全名及主要別名；新增 ThermalProtect 實際關機觸發、ThermalProtect 小機殼走線限制、ROG Equalizer 約 960～980W 的未量化單機觀察，以及 PMD2X 對 GPU Shield 的功能比較。產品使用經驗、留言推論與競品內容已分開標示。'),
    ('2026-10-07', 'Tom’s Hardware、ComputerBase、Hardwareluxx、Overclockers UK、PCGH Extreme、Chiphell、NGA玩家社區與百度貼吧：以 2026-09-29 之後日期、產品全名及中德英在地用語補查公開可讀結果；本輪未找到可新增、且能完整核讀主文與留言的唯一討論，未把搜尋雜訊或只有摘要的頁面納入。'),
    ('2026-09-29', 'Hardwareluxx：逐頁核讀本週兩筆 WireView 討論：Noctua Edition 使用者測試與 Wired 版主機板電源按鈕 splitter 接頭脫落／原廠換貨回覆；前者納入約 20°C、模組峰值約 44°C、強制風扇後表面溫度下降約 6°C 等單機資料，後者標示為單一安裝個案。'),
    ('2026-09-29', 'Chiphell：逐頁核讀 9/28 的 WireView Pro II Noctua Edition 轉貼串與 10 則可見留言；主文是 IT之家發布資料的轉貼，留言主要質疑額外轉接設備、價格與產品定位，沒有新增實機量測或保護觸發證據。'),
    ('2026-09-29', '百度貼吧、NGA玩家社區、ComputerBase、Overclockers UK、PCGH Extreme：以本週日期與產品／在地用語重新查找；百度顯卡吧找到 9/24「燒接口5090」與 9/23 供電線問題，但前者可讀正文沒有提供足夠的產品／測試細節，後者是一般 8-pin 問題，均不納入 12V-2x6 明細；NGA搜尋介面本輪仍未穩定回傳關鍵字結果，其他論壇未找到可直接新增且已完整核讀的本週唯一討論。'),
    ('2026-09-29', 'Reddit：補查 2026-09-24～2026-09-28 的公開搜尋結果與可讀頁面，逐篇核讀 6 筆唯一討論及可見留言，新增 WireView 的 6-wire 監控範圍、Noctua Edition 價格／風扇／Linux／相容性、風扇更換、垂直安裝，以及一件 91.7°C 接頭事件中對 OptiGuard 的個人推薦；後者沒有 OptiGuard 實測，未作效果推論。'),
    ('2026-09-29', 'TechPowerUp：在 Chrome 的站內搜尋以「WireView」及「Newer than 2026-09-23」、依日期排序查找，逐頁閱讀 9/28 的 Thermal Grizzly／Noctua WireView Pro II 討論串及可見留言，新增 1 筆；官方發布資料與使用者留言分開記錄，未把官方測試數據當成使用者實測。'),
    ('2026-09-23', 'Reddit：補查 2026-09-13～2026-09-22 的公開搜尋結果與可讀頁面，逐篇核讀 6 筆唯一討論及可見留言，新增 ROG Equalizer／WireView、GPU Safeguard、GPU Shield、Ampinel、ThermalProtect 資料；跨版重貼排除。因部分直接頁面仍受快取／擴充功能限制，未把搜尋不到解讀為沒有討論。'),
    ('2026-09-23', 'TechPowerUp：用「Newer than」= 2026-09-16、依日期排序，核讀全部 12 個關鍵字。「Close call... 5090 Burnt Cable」長串本週最活躍，新增 ThermalProtect／ROG Equalizer 相容性與規格比較（3-dimple vs. 4-spring 端子）、引用 igorslab.de 對 Equalizer 端子壁厚度的機構質疑，以及 Dr. Dro 對「理想安全線材」的個人構想（結合 Equalizer 高承載設計＋ThermalProtect 溫度斷電＋可重置保險絲，目前無任何產品如此設計）。另有新討論串：DLSS 5 導致當機的使用者被建議加裝 ThermalProtect／ROG Equalizer；EZDIY-FAB Alpha TS13 在一篇 mini-ITX 改裝完工文中確認成功安裝。GPU Safeguard、OptiGuard、Titanload、T-Guard、GPU Tweak III Auto-Shutdown、GPU Shield 本次查核沒有找到新內容；ASRock TempGuard 相關討論串本週僅有大量重複性意見交鋒，沒有可查核的新事實，故本輪未收錄。'),
    ('2026-09-23', 'PCGH Extreme：用「Neuer als」= 2026-09-16 核讀 WireView／Ampinel／ROG Equalizer／ThermalProtect／GPU Shield。新增一起 PNY RTX 5090 於 2D／低負載情境下 16-pin 接頭熔損的案例（PNY 拒絕保固），留言者引用 IgorsLab／der8auer 的見解說明此類熔損與負載高低關聯較小、主因是接頭端子設計本身，並首次提出「即使加裝 WireView，廠商仍可能反過來以『問題出在 WireView』為由拒絕保固」的疑慮（屬個人推測，無實際案例佐證）。另有上週 FurMark 測試使用者 ParrotHH 的後續回覆，確認已為 RTX 5090 FE 加裝 WireView 2 Pro（與 4090 上的 Ampinel 並用），純屬購買計畫完成與主觀心得，無新量測數據。Reddit：本次因瀏覽器擴充功能的安全限制無法連線（整個 reddit.com 網域被封鎖，並非個別頁面的同意視窗問題），本輪未能查核，下次再補。'),
    ('2026-09-16', 'TechPowerUp：用「Newer than」= 2026-09-08、依日期排序，核讀全部 12 個關鍵字，新增本週最重大事件——Cooler Master GPU Shield 正式美國上市（同串涉及 WireView／ROG Equalizer／Ampinel／ThermalProtect 的跨產品比較與 ASUS 17A 額定質疑），以及 ASRock TempGuard 未能攔截 15,000 美元 RTX PRO 6000 熔損事故（技師指出感測器裝在接地側而非 12V 側）；另補充 EZDIY-FAB Alpha TS13 討論串本週延伸的 Ampinel 比較與 AIB／Nvidia 責任歸屬辯論，以及「Close call... 5090 Burnt Cable」長串中 Dr. Dro 的 ThermalProtect 電壓降觀察。GPU Tweak III Auto-Shutdown、Titanload、T-Guard、OptiGuard、GPU Safeguard 本次查核沒有找到新內容。'),
    ('2026-09-16', 'Reddit：追查 TechPowerUp TempGuard 報導所引用的原始 r/ASRock 貼文，新增留言者對「感測器位置不足以偵測」的技術質疑與 ASUS Astral 逐 pin 監控的提及。PCGH Extreme：用「Neuer als」= 2026-09-08 核讀 Ampinel，新增使用者 FurMark 實測 40% 逐 pin 電流不平衡、Ampinel 主動介入均流的具體案例。'),
    ('2026-09-09', 'PCGH Extreme：首次嘗試因網站訂閱／廣告同意視窗卡住頁面，使用者手動處理該視窗後重試成功；核讀 WireView 新增 1 筆——同一起 DLSS 5 熔損事件在德語論壇的獨立討論，並提供與 Hardware Unboxed 事件相符的跨論壇佐證（同一位「擁有贊助 WireView 卻沒使用」的知名 YouTuber）。'),
    ('2026-09-09', 'TechPowerUp：改用「Newer than」欄位直接篩選 2026-09-02 之後、依日期排序，核讀全部關鍵字，新增本週兩起重大熔損事件報導（DLSS 5 測試熔損、Hardware Unboxed 自家測試機台熔損，後者同時涉及 WireView／ROG Equalizer／GPU Tweak III Auto-Shutdown／ThermalProtect）。Reddit：以 r/ThermalGrizzly 限定＋t=week 核讀 WireView，新增風扇異音案例（含原廠 RMA 率回覆）。'),
    ('2026-09-02', '修正對 Reddit 搜尋失效原因的誤判——問題並非需要登入，而是 sort=new（依日期排序）參數本身失效，不論登入與否都會跳轉回與關鍵字無關的 r/all 最新內容；移除該參數、改用 relevance 排序（並視需要加上 subreddit 限定與 t=month/week）即可取得真實結果，用此方式核讀全部 11 個關鍵字。「四、使用者評價與改善方向」已依當輪新收錄的 TechPowerUp／Tom’s Hardware／Reddit／PCGH Extreme 明細重新整理 WireView、Ampinel、GPU Shield、ROG Equalizer、ThermalProtect 五張卡片的本週更新（含來源連結）；沒有新證據的產品維持原卡片內容，不強行補新內容。'),
    ('2026-09-02', '核讀 TechPowerUp（10 個關鍵字全查）與 Tom’s Hardware（WireView）自上版以來的新內容，新增 8 筆明細；ComputerBase、Hardwareluxx、NGA玩家社區、Chiphell、百度貼吧、Overclockers UK、PCGH Extreme 當輪未查核。'),
]
version_history_rows = ''.join(
    f'<li><b>{escape(v)}</b>｜{escape(d)}：{escape(desc)}</li>' for v, d, desc in version_history
)
update_log_rows = ''.join(
    f'<li><b>{escape(d)}</b>：{escape(desc)}</li>' for d, desc in update_log
)
period_start_label = PERIOD_START.isoformat()
period_end_label = PERIOD_END.isoformat()
latest_reddit_date = max(row['date'] for row in rows if row['source'] == 'Reddit')
if new_rows:
    new_source_counts = Counter(row['source'] for row in new_rows)
    new_keyword_counts = Counter(keyword for row in new_rows for keyword in row['keywords'])
    source_summary = '、'.join(f'{source} {count} 篇' for source, count in new_source_counts.items())
    keyword_summary = '、'.join(
        f'{keyword_display_names.get(keyword, keyword)} {count} 篇'
        for keyword, count in new_keyword_counts.most_common()
    )
    focus_items = ''.join(
        '<article class="focus-card"><div class="focus-meta"><span>{date}</span><span>{source}</span>'
        '<span class="focus-keyword">{keywords}</span></div><h3>{title}</h3>'
        '<p>{summary}</p><div class="focus-comment"><b>留言重點</b>{comments}</div></article>'.format(
            date=escape(row['date']),
            source=escape(row['source']),
            keywords='、'.join(
                escape(keyword_display_names.get(kwn, kwn)) + (' <span class="new-badge">New!</span>' if kwn in new_keywords else '')
                for kwn in row['keywords']
            ),
            title=escape(row['title']),
            summary=escape(row['summary']),
            comments=escape(row['comments']),
        )
        for row in new_rows[:6]
    )
    if len(new_rows) > 6:
        focus_items += f'<div class="focus-more">其餘 {len(new_rows) - 6} 篇新增內容請見下方標示 <span class="new-badge">New!</span> 的明細。</div>'
    weekly_focus = (
        '<div class="focus-summary">'
        f'<div><span>本版新增（前版比對）</span><b>{len(new_rows)} 篇</b></div>'
        f'<div><span>來源分布</span><b>{escape(source_summary)}</b></div>'
        f'<div><span>涉及產品</span><b>{escape(keyword_summary)}</b></div>'
        '</div>'
        f'<div class="focus-grid">{focus_items}</div>'
    )
else:
    weekly_focus = (
        '<div class="focus-empty"><b>本版新增 0 篇</b><span>依明細連結比對，目前內容均已存在於前一版報告；本區不延伸推測新的市場趨勢。</span></div>'
    )

overview_cards = ''.join(
    '<article class="product-card"><div class="product-head"><div><span class="product-vendor">{vendor}</span>'
    '<h3>{keyword} {new_badge}</h3></div><span class="product-type">{category}</span></div>'
    '<div class="product-meta"><span><b>型態</b>{form_factor}</span><span><b>偵測</b>{detection}</span></div>'
    '<p>{function}</p></article>'.format(
        vendor=escape(keyword_vendor[k]),
        keyword=escape(keyword_display_names[k]),
        new_badge='<span class="new-badge">New!</span>' if k in new_keywords else '',
        category=escape(keyword_category[k]),
        form_factor=escape(product_form_factor[k]),
        detection=escape(product_detection[k]),
        function=escape(keyword_info[k][0]),
    ) for k in kw
)

html = f'''<!doctype html>
<html lang="zh-Hant"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<link rel="icon" type="image/png" href="thebigcoco-coconut-logo.png">
<title>12V-2x6 保護產品每週論壇報告（{generated_at_label}）</title>
<style>
:root{{--bg:#f5f6f8;--card:#fff;--ink:#1c2330;--muted:#68758a;--line:#e3e7ee;--accent:#2563eb;--warn:#fff8e6;--orange:#b45309}}
*{{box-sizing:border-box}} html{{scroll-behavior:smooth}} body{{margin:0;background:var(--bg);color:var(--ink);font:14px/1.55 "Segoe UI","Microsoft JhengHei",sans-serif}}
.wrap{{max-width:1840px;margin:auto;padding:20px 24px 60px}} header{{display:flex;flex-wrap:wrap;gap:12px;align-items:center}} .brand-title{{display:flex;align-items:center;gap:12px}} .brand-logo{{width:48px;height:48px;object-fit:contain;flex:none}} .brand-copy h1{{font-size:21px;margin:0 0 3px}} .meta{{font-size:12.5px;color:var(--muted)}}
.note{{background:var(--warn);border:1px solid #f1e3a6;border-radius:8px;padding:11px 14px;margin:14px 0;font-size:13px}} .tabs{{display:flex;gap:8px;margin:14px 0}} .tab{{padding:7px 18px;border-radius:999px;border:1px solid var(--line);background:var(--card);font-weight:600}} .tab.active{{background:var(--accent);color:#fff}}
.statbar{{display:flex;gap:12px;flex-wrap:wrap;margin:12px 0}} .stat{{background:var(--card);border:1px solid var(--line);border-radius:10px;padding:10px 18px;min-width:130px}} .stat b{{font-size:20px;display:block}} .stat span{{font-size:12px;color:var(--muted)}}
section{{margin:20px 0;scroll-margin-top:16px}} h2{{font-size:17px;border-left:4px solid var(--accent);padding-left:10px}} .section-range{{display:inline-block;margin-left:7px;padding:2px 8px;border-radius:999px;background:#eef1f6;color:var(--muted);font-size:11.5px;font-weight:600;vertical-align:2px}} table{{border-collapse:collapse;background:var(--card);width:100%;border:1px solid var(--line)}} th,td{{padding:8px 10px;border-bottom:1px solid var(--line);text-align:left;vertical-align:top}} th{{background:#eef1f6;white-space:nowrap;font-size:12.5px}} td.dt{{white-space:nowrap}} td.ti{{min-width:300px;font-weight:600}} td.sm{{min-width:280px;color:#333}} td.issue-cell{{min-width:140px}} .num{{text-align:right}} .badge{{display:inline-block;margin:1px 2px 1px 0;padding:2px 8px;border-radius:999px;background:#e8f0fe;color:#1d4ed8;font-size:12px}} .issue-tag{{display:inline-block;margin:1px 2px 3px 0;padding:3px 7px;border-radius:6px;background:#fff1e8;color:#b54708;border:1px solid #f2c7a5;font-size:11.5px;line-height:1.25}} .issue-none{{color:#9aa3af}} a{{color:var(--accent);text-decoration:none}} a:hover{{text-decoration:underline}} .muted{{color:var(--muted)}} ul{{margin-top:6px}}
.focus-summary{{display:grid;grid-template-columns:160px minmax(230px,1fr) minmax(320px,2fr);gap:10px;margin-bottom:12px}} .focus-summary>div{{display:flex;flex-direction:column;gap:3px;background:linear-gradient(135deg,#eff6ff,#fff);border:1px solid #cfe0ff;border-radius:10px;padding:11px 14px}} .focus-summary span{{font-size:11.5px;color:var(--muted);font-weight:600}} .focus-summary b{{font-size:14px;color:#173b7a}} .focus-summary>div:first-child b{{font-size:22px;color:var(--accent)}}
.focus-grid{{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:12px}} .focus-card{{background:var(--card);border:1px solid var(--line);border-radius:11px;padding:14px;box-shadow:0 2px 8px rgba(35,52,78,.04)}} .focus-card h3{{font-size:15px;line-height:1.4;margin:8px 0 7px}} .focus-card p{{margin:0 0 10px;color:#303b4c}} .focus-meta{{display:flex;align-items:center;gap:6px;flex-wrap:wrap}} .focus-meta span{{font-size:11.5px;background:#eef1f6;color:#526075;border-radius:999px;padding:2px 7px}} .focus-meta .focus-keyword{{background:#e8f0fe;color:#1d4ed8}} .focus-comment{{border-left:3px solid #9ab8f5;background:#f7f9fd;border-radius:0 7px 7px 0;padding:8px 10px;color:#58657a;font-size:12.5px}} .focus-comment b{{display:block;color:#30486f;font-size:11.5px;margin-bottom:2px}} .focus-more{{grid-column:1/-1;text-align:center;background:#fff7ed;border:1px dashed #fdba74;border-radius:9px;padding:9px;color:#9a4b08}} .focus-empty{{display:flex;gap:10px;align-items:center;background:var(--card);border:1px solid var(--line);border-radius:10px;padding:15px}} .focus-empty b{{color:var(--accent)}} .focus-empty span{{color:var(--muted)}}
.product-grid{{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:11px}} .product-card{{background:var(--card);border:1px solid var(--line);border-radius:11px;padding:13px 15px}} .product-card:hover{{border-color:#b8caf0;box-shadow:0 3px 10px rgba(35,52,78,.05)}} .product-head{{display:flex;gap:12px;justify-content:space-between;align-items:flex-start;margin-bottom:7px}} .product-head h3{{font-size:15.5px;line-height:1.25;margin:2px 0 0;color:#183f83}} .product-vendor{{display:block;color:var(--muted);font-size:11.5px;font-weight:600}} .product-type{{max-width:48%;background:#f0f4fa;color:#4c5e78;border-radius:7px;padding:4px 7px;font-size:11px;line-height:1.35;text-align:right}} .product-card p{{margin:0;color:#374151;line-height:1.6}}
.product-meta{{display:flex;flex-wrap:wrap;gap:7px;margin:0 0 9px}} .product-meta span{{display:inline-flex;gap:5px;align-items:center;border:1px solid #d8e1ee;border-radius:999px;background:#f8fafc;color:#334155;padding:3px 8px;font-size:11.5px}} .product-meta b{{color:#1d4ed8;font-size:10.5px}}
.evidence{{display:inline-block;color:#7c2d12;background:#ffedd5;border-radius:6px;padding:3px 8px;font-size:11.5px;white-space:nowrap}} .pm-priorities{{display:grid;grid-template-columns:repeat(3,minmax(230px,1fr));gap:10px;margin:10px 0 14px}} .pm-card{{background:var(--card);border:1px solid var(--line);border-radius:9px;padding:11px 13px}} .pm-card b{{display:block;margin-bottom:4px;color:#1d4ed8}}
.pm-products{{display:grid;gap:14px}} .pm-product{{background:var(--card);border:1px solid #d9e0ea;border-radius:12px;overflow:hidden;box-shadow:0 3px 12px rgba(35,52,78,.05)}} .pm-product-head{{display:flex;justify-content:space-between;align-items:center;gap:12px;padding:13px 16px;background:linear-gradient(135deg,#f5f8ff,#fff);border-bottom:1px solid var(--line)}} .pm-product-head h3{{display:flex;align-items:center;gap:8px;margin:2px 0 0;font-size:17px;color:#173b7a}} .pm-kicker{{font-size:10.5px;font-weight:700;letter-spacing:.08em;color:var(--muted)}} .pm-aspects{{display:grid;grid-template-columns:repeat(3,minmax(0,1fr))}} .pm-aspect{{margin:0;padding:14px 16px;border-right:1px solid var(--line)}} .pm-aspect:last-child{{border-right:0}} .pm-aspect h4{{margin:0 0 9px;padding:0 0 7px;border-bottom:2px solid;font-size:13px}} .pm-positive h4{{color:#166534;border-color:#86c99a}} .pm-negative h4{{color:#991b1b;border-color:#efaaaa}} .pm-action h4{{color:#1d4ed8;border-color:#9ab8f5}} .pm-list{{margin:0;padding-left:18px;color:#374151}} .pm-list li{{margin:0 0 7px;padding-left:2px;line-height:1.62}} .pm-list li:last-child{{margin-bottom:0}} .pm-list li::marker{{color:#8090a8}} .pm-empty{{margin:0;color:var(--muted);font-style:italic}} .pm-new{{margin-top:11px;padding:10px 11px;background:#fff8ed;border:1px solid #fed7aa;border-radius:8px}} .pm-new-title{{display:flex;align-items:center;gap:6px;margin-bottom:7px;color:#9a4b08;font-size:12px}} .pm-new .pm-list{{color:#533b26}} .pm-history-group{{margin-top:9px}} .pm-history-group>b{{display:block;margin-bottom:5px;color:#7c4a18}} .pm-history-group .new-badge{{margin-right:5px}} .pm-new-source{{margin-top:7px;font-size:12px;line-height:1.7}} .pm-new-source>.new-badge{{margin-right:5px}} .pm-new-source>b{{color:#9a4b08}} .pm-evidence{{display:flex;align-items:flex-start;gap:12px;padding:10px 16px;background:#fafbfc;border-top:1px solid var(--line);font-size:12px}} .pm-evidence>a{{font-weight:600;white-space:nowrap}} .pm-evidence .pm-new-source{{margin:0;padding-left:12px;border-left:1px solid var(--line)}}
.new-badge{{display:inline-block;padding:2px 7px;border-radius:999px;background:#dc2626;color:#fff;font-size:11px;font-weight:700;vertical-align:1px}} .revision-history{{margin-top:26px;padding:13px 16px;background:var(--card);border:1px solid var(--line);border-radius:10px}} .revision-history h2{{margin:0 0 8px;font-size:15px}} .revision-history ul{{margin:0;padding-left:20px}} .revision-history b{{color:#1d4ed8}}
.filters{{display:grid;gap:10px;margin:0 0 12px;padding:12px;background:var(--card);border:1px solid var(--line);border-radius:10px}} .filter-group{{display:grid;grid-template-columns:62px 1fr;gap:10px;align-items:start}} .filter-label{{padding-top:6px;font-size:12px;color:var(--muted);font-weight:600}} .chips{{display:flex;flex-wrap:wrap;gap:7px}} .filter-chip{{border:1px solid var(--line);border-radius:999px;background:#fff;color:var(--ink);padding:5px 11px;font:inherit;font-size:12.5px;cursor:pointer}} .filter-chip:hover{{border-color:#93b4f4;background:#f5f8ff}} .filter-chip.active{{border-color:var(--accent);background:var(--accent);color:#fff}} .new-filter{{color:#b91c1c;border-color:#fecaca;font-weight:700}} .new-filter.active{{border-color:#b91c1c;background:#dc2626;color:#fff}} .result-count{{color:var(--muted);font-size:12.5px;text-align:right}} tr[hidden]{{display:none}}
.load-more-row{{display:flex;justify-content:center;padding:14px 0}} .load-more-btn{{border:1px solid var(--accent);border-radius:999px;background:#fff;color:var(--accent);padding:8px 22px;font:inherit;font-size:13px;font-weight:600;cursor:pointer}} .load-more-btn:hover{{background:var(--accent);color:#fff}} .load-more-btn[hidden]{{display:none}}
@media(max-width:900px){{.wrap{{padding:14px}}.tblbox{{overflow-x:auto}}table{{min-width:1200px}}.pm-priorities,.focus-grid,.product-grid{{grid-template-columns:1fr}}.focus-summary{{grid-template-columns:1fr}}.focus-more{{grid-column:auto}}.pm-product-head{{align-items:flex-start;flex-direction:column}}.pm-product-head .evidence{{width:100%;white-space:normal}}.pm-aspects{{grid-template-columns:1fr}}.pm-aspect{{border-right:0;border-bottom:1px solid var(--line)}}.pm-aspect:last-child{{border-bottom:0}}.pm-evidence{{display:block}}.pm-evidence .pm-new-source{{margin-top:8px;padding:8px 0 0;border-left:0;border-top:1px solid var(--line)}}}} @media(max-width:600px){{.brand-title{{align-items:flex-start}}.brand-logo{{width:42px;height:42px}}}}
</style></head><body><div class="wrap">
<header><div class="brand-title"><img class="brand-logo" src="thebigcoco-coconut-logo.png" alt="TheBigCoco 椰子標誌"><div class="brand-copy"><h1>12V-2x6 / 12VHPWR 保護產品 — 每週論壇報告</h1><span class="meta"><b>{REPORT_VERSION}</b>｜產生時間：<b>{generated_at_label}</b>｜上次更新時間：<b>{escape(previous_generated_at_label)}</b>｜資料期間：{period_start_label}～{period_end_label}</span></div></div></header>
<div class="statbar"><div class="stat"><b>{len(rows)}</b><span>有效明細</span></div><div class="stat"><b>{sum(bool(r.get('reviewed')) for r in rows)}</b><span>已核讀明細</span></div><div class="stat"><b>{len(new_rows)}</b><span>本週New</span></div><div class="stat"><b>{sum(r['source']=="Tom's Hardware Forums" for r in rows)}</b><span>Tom's Hardware</span></div><div class="stat"><b>{sum(r['source']=='Reddit' for r in rows)}</b><span>Reddit（已驗證）</span></div><div class="stat"><b>{sum(r['source']=='TechPowerUp Forums' for r in rows)}</b><span>TechPowerUp</span></div><div class="stat"><b>{sum(r['source']=='ComputerBase Forum' for r in rows)}</b><span>ComputerBase</span></div><div class="stat"><b>{sum(r['source']=='Hardwareluxx Forum' for r in rows)}</b><span>Hardwareluxx</span></div><div class="stat"><b>{sum(r['source']=='Overclockers UK Forums' for r in rows)}</b><span>Overclockers UK</span></div><div class="stat"><b>{sum(r['source']=='PC Games Hardware Extreme' for r in rows)}</b><span>PCGH Extreme</span></div><div class="stat"><b>{sum(r['source']=='NGA玩家社區' for r in rows)}</b><span>NGA玩家社區</span></div><div class="stat"><b>{sum(r['source']=='Chiphell' for r in rows)}</b><span>Chiphell</span></div><div class="stat"><b>{sum(r['source'].startswith('百度貼吧') for r in rows)}</b><span>百度貼吧</span></div></div>
<div class="tabs"><a class="tab active" href="#weekly-focus">本週焦點</a><a class="tab" href="#overview">重點觀察</a><a class="tab" href="#details">搜尋結果明細</a></div>
<section id="weekly-focus"><h2>一、本週焦點 <span class="section-range">{escape(weekly_focus_range)}</span></h2>{weekly_focus}</section>
<div class="tabs"><a class="tab" href="#weekly-focus">本週焦點</a><a class="tab" href="#overview">重點觀察</a><a class="tab" href="#details">搜尋結果明細</a></div>
<section id="overview"><h2>二、目前可由實際內容確認的產品功能重點</h2><div class="product-grid">{overview_cards}</div></section>
<div class="tabs"><a class="tab" href="#weekly-focus">本週焦點</a><a class="tab" href="#overview">重點觀察</a><a class="tab" href="#details">搜尋結果明細</a></div>
<section><h2>三、關鍵字功能與有效結果數</h2><div class="tblbox"><table><thead><tr><th>關鍵字</th><th>廠商</th><th>產品類別</th><th>功能說明</th><th>搜尋別名／型號</th><th>有效明細數</th><th>資料來源</th></tr></thead><tbody>{kw_rows}</tbody></table></div></section>
<div class="tabs"><a class="tab" href="#weekly-focus">本週焦點</a><a class="tab" href="#overview">重點觀察</a><a class="tab" href="#details">搜尋結果明細</a></div>
<section id="reviews"><h2>四、使用者評價與改善方向</h2>
<div class="note"><b>判讀規則：</b>「優點／缺點」只整理實際讀到的使用者經驗與看法；產品發布文字不當成使用者評價。「改善方向」是由已讀痛點轉換成的產品需求，不代表留言者原句。單一個案、跨論壇重複轉貼與未驗證圖片不推論為普遍結果；留言者對故障原因的推測不寫成事實；正反經驗並列；沒有使用者實測的產品明確標示證據不足。表格內的 <span class="new-badge">New!</span> 代表該句依本版新增貼文／留言補入，並於證據欄列出本週來源；沒有新證據的產品不新增評價。<br><b>優先等級：</b>P0＝最高優先，涉及安全、硬體損壞或核心保護失效；P1＝重要，影響可靠性、驗證能力或安裝使用體驗；P2＝一般，影響價格合理性、相容性或使用便利性，可排入後續改善。</div>
<div class="pm-priorities">
  <div class="pm-card"><b>P0｜保護後的自動處置</b>使用者不只需要警告，也希望能在異常時降功率或關機；應明確定義門檻、反應時間與失效安全模式。</div>
  <div class="pm-card"><b>P0｜接頭本身的可靠性</b>額外轉接點、重量、插拔循環與 PSU／GPU 兩端失效，都是重複出現的疑慮。</div>
  <div class="pm-card"><b>P1｜可驗證與可追溯</b>公布量測誤差、per-pin 電流、溫升、長時間負載及插拔壽命，並保留警報／關機事件紀錄。</div>
  <div class="pm-card"><b>P1｜整合式防護</b>留言傾向期待均流、溫度感測、電流監控與 failsafe 結合，而非只有被動強化或資訊顯示。</div>
  <div class="pm-card"><b>P1｜機構與相容性</b>降低接頭高度、重量與首段彎折需求，避免高階顯示卡搭配一般機殼時無法正確安裝。</div>
  <div class="pm-card"><b>P2｜價值與使用門檻</b>降低對專用軟體、特定 PSU 或藍牙的依賴，並用測試數據說明售價與保護價值。</div>
</div>
<div class="pm-products">{pm_cards}</div>
</section>
<div class="tabs"><a class="tab" href="#weekly-focus">本週焦點</a><a class="tab" href="#overview">重點觀察</a><a class="tab" href="#details">搜尋結果明細</a></div>
<section id="details"><h2>五、搜尋結果明細</h2>
<div class="note"><b>日期定義：</b>明細日期為原始貼文或指定樓層留言的發布日期，不是加入報告的時間；報告產生時間另列於頁首。</div>
<div class="filters">
  <div class="filter-group"><span class="filter-label">關鍵字</span><div class="chips" id="keywordChips"><button type="button" class="filter-chip active" data-value="">全部</button>{keyword_chips}</div></div>
  <div class="filter-group"><span class="filter-label">論壇</span><div class="chips" id="forumChips"><button type="button" class="filter-chip active" data-value="">全部</button>{forum_chips}</div></div>
  <div class="filter-group"><span class="filter-label">月份</span><div class="chips" id="monthChips"><button type="button" class="filter-chip active" data-value="">全部</button>{month_chips}</div></div>
  <div class="filter-group"><span class="filter-label">版本</span><div class="chips" id="newChips"><button type="button" class="filter-chip active" data-value="">全部</button><button type="button" class="filter-chip new-filter" data-value="1">New!</button></div></div>
  <div class="result-count">顯示 <b id="visibleCount">{len(rows)}</b>／<span id="matchedCount">{len(rows)}</span> 筆</div>
</div>
<div class="note">本次問題標籤已逐筆讀取主文與可見留言後人工覆核；只有來源明確提到的問題才標示。驗證頁、空白頁或只有一般規格／風險討論者不把推測寫成故障；「—」表示本筆未讀到可確認的產品問題，不代表產品絕對沒有問題。</div><div class="tblbox"><table id="detailTable"><thead><tr><th>發文日期（新到舊）</th><th>來源</th><th>關鍵字</th><th>命中位置</th><th>標題</th><th>問題標籤</th><th>主文內容（發生什麼）</th><th>留言結論／使用者評價</th><th>連結</th></tr></thead><tbody>{detail}</tbody></table></div>
<div class="load-more-row"><button type="button" id="loadMoreBtn" class="load-more-btn" hidden>顯示更多</button></div></section>
<div class="tabs"><a class="tab" href="#weekly-focus">本週焦點</a><a class="tab" href="#overview">重點觀察</a><a class="tab" href="#details">搜尋結果明細</a></div>
<section class="muted"><h2>六、搜尋來源狀態</h2><ul><li>Reddit：納入 {sum(r['source']=='Reddit' for r in rows)} 篇唯一討論串；最新可核對結果為 {latest_reddit_date}。本日合併更新相較 2026-10-20 基準新增／補收 12 篇；PinProtect 專項增加第二代 RM1200e 與整合式 PSU 比較 2 篇，並把 2 篇既有比較串重分類到 PinProtect／PinProtect+。逐篇展開可見留言，跨版重貼排除。</li><li>Tom's Hardware Forums：納入 {sum(r['source']=="Tom's Hardware Forums" for r in rows)} 筆；補查 PinProtect、RM1200e、HX1000i SHIFT CRYSTAL 與 12V-2x6 事故詞，未找到可新增且已完整核讀的唯一討論。</li><li>TechPowerUp Forums：納入 {sum(r['source']=='TechPowerUp Forums' for r in rows)} 筆；Chrome 登入狀態正常，除振華 OCP Dongle 外，新增完整核讀的 RM1200e PinProtect 發表串與 8 則回覆；Computex 串的 5 則回覆皆在討論機殼，未誤列為 PinProtect 使用評價。</li><li>ComputerBase Forum：納入 {sum(r['source']=='ComputerBase Forum' for r in rows)} 筆；PinProtect 專項補收 2026-06-02 的兩頁、32 則留言完整討論，產品功能、技術觀點與使用者疑慮分開記錄。</li><li>Hardwareluxx Forum：納入 {sum(r['source']=='Hardwareluxx Forum' for r in rows)} 筆；重新完整核讀並重分類既有 2026-06-05 PinProtect／PinProtect+ 討論，沒有擁有者觸發案例。</li><li>Overclockers UK Forums：納入 {sum(r['source']=='Overclockers UK Forums' for r in rows)} 筆；PinProtect 專項補查未找到可新增且已完整核讀的唯一討論。</li><li>PC Games Hardware Extreme：納入 {sum(r['source']=='PC Games Hardware Extreme' for r in rows)} 筆；PinProtect 專項補查未找到可新增且已完整核讀的唯一討論。</li><li>NGA玩家社區：納入 {sum(r['source']=='NGA玩家社區' for r in rows)} 筆 2025-07-01 以後資料；以 PinProtect、RM1200e、海盜船逐針腳／單 pin 過流保護等詞補查，未把空白或不穩定搜尋結果當成沒有討論。</li><li>Chiphell：納入 {sum(r['source']=='Chiphell' for r in rows)} 筆 2025-07-01 以後資料；重新核讀並重分類既有 2026-07-20 海盜船保護方案討論，沒有擁有者觸發案例。</li><li>百度貼吧：納入 {sum(r['source'].startswith('百度貼吧') for r in rows)} 筆 2025-07-01 以後資料；以 PinProtect、RM1200e、海盜船逐針腳／單 pin 過流保護等詞補查公開可讀結果，未找到可新增且已完整核讀的唯一討論。</li></ul></section>
<div class="tabs"><a class="tab" href="#weekly-focus">本週焦點</a><a class="tab" href="#overview">重點觀察</a><a class="tab" href="#details">搜尋結果明細</a></div>
<section class="muted"><h2>七、Reddit 精確度與廣度確認</h2><ul><li><b>範圍：</b>以 {period_start_label}～{period_end_label} 為日期界線，交叉查找產品全名、常見拼法、完整 PSU／線材型號、配件料號、per-pin／telemetry／NTC／thermistor／保護功能詞、12V-2x6／12VHPWR 事故語句，以及標題沒有產品名的主文與留言。</li><li><b>固定查詢線：</b>{escape('；'.join(reddit_required_query_lanes))}。PinProtect 另加入 RM1200e Gen 2、CP-9020316／CP-9020317、HX1000i SHIFT CRYSTAL、per-pin OCP 與海盜船逐針腳／單 pin 過流保護。本次同時讀取貼文與 Comments 分頁。</li><li><b>本次覆蓋稽核：</b>本日合併更新相較 2026-10-20 基準新增／補收 12 篇 Reddit 唯一討論；PinProtect 專項新增 2 篇唯一明細並重分類 2 篇既有比較串。納入 URL 由產生器自動對帳，主文與可見留言分開摘要。</li><li><b>漏網原因與修正：</b>只搜尋 PinProtect 會漏掉標題只寫 RM1200e 或泛稱 12V GPU 接頭、但內文／留言才出現功能名稱的文章；因此固定加入完整 PSU 型號、料號、per-pin OCP 與 Comments 分頁交叉查找。</li><li><b>精確度：</b>實際持有／安裝、購買考量、官方功能、留言觀點與推測分開記錄；本次沒有 PinProtect／PinProtect+ 擁有者觸發、燒毀或熔毀案例，不能把推薦或發布資訊寫成保護效果已驗證。</li><li><b>限制：</b>Reddit 搜尋可能延遲索引、動態載入或省略部分回覆；留言摘要只代表本次實際可見內容，不把未載入內容或搜尋空白推論為沒有討論。</li></ul></section>
<div class="tabs"><a class="tab" href="#weekly-focus">本週焦點</a><a class="tab" href="#overview">重點觀察</a><a class="tab" href="#details">搜尋結果明細</a></div>
<section class="revision-history"><h2>版本紀錄（架構變動）</h2><div class="note" style="margin-top:0">只記錄新增論壇來源、新增／調整追蹤關鍵字、版型或篩選功能調整這類架構層級變動；逐次的查核與新增明細請見下方「內容更新紀錄」。</div><ul>{version_history_rows}</ul></section>
<section class="revision-history"><h2>內容更新紀錄</h2><div class="note" style="margin-top:0">記錄每次查核實際跑了哪些來源／關鍵字、找到並新增了什麼；不對應版本號，同一版本號下可能有多筆更新紀錄。</div><ul>{update_log_rows}</ul></section>
<div class="note"><b>方法與限制：</b>搜尋範圍包含標題、主文及留言；標題未出現產品名，只要內文或留言完整命中且可排除同名產品，也會納入。每項產品以產品全名、品牌／型號、功能情境交叉查找；Reddit 另分別檢視 Relevance、New 與 Comments。ComputerBase 與 Hardwareluxx 以站內可讀討論頁及站外索引交叉查找後，再逐頁閱讀。結果逐一記錄「納入／排除原因」，再以標準化 URL 與報告明細對帳。產生器若發現已判定納入的 URL 不在明細中，會直接中止。本版共收錄 {len(rows)} 筆已核讀主文與頁面可見留言。摘要只寫可見內容，不做臆測；無留言、跨站轉貼、未驗證圖片、單一使用者設定或留言者推測均會明確標示。Reddit 的「更多回覆」與未載入留言可能無法完整讀取，因此留言摘要代表本次可見內容，不代表整串所有留言。已排除 OptiGuard 殺蟲劑／電梯零件、其他用途的 T-Guard，以及散熱護罩類 GPU shield。<br><b>前版比對：</b>{escape(previous_report_label)}；以明細的標準化連結判定 New!，不使用標題文字比對。{'' if previous_report else '本次找不到前版，因此不將既有資料全部標為 New!。'}</div>
<footer class="muted">本報告只反映本次可讀取且通過關鍵字與同名產品排除規則的內容；有效明細不足不代表論壇沒有相關討論。</footer>
<script>
const detailRows = [...document.querySelectorAll('#detailTable tbody tr')];
const visibleCount = document.getElementById('visibleCount');
const matchedCount = document.getElementById('matchedCount');
const loadMoreBtn = document.getElementById('loadMoreBtn');
const PAGE_SIZE = 10;
let selectedKeyword = '';
let selectedForum = '';
let selectedMonth = '';
let selectedNew = '';
let shownCount = PAGE_SIZE;
function applyFilters() {{
  const matched = detailRows.filter(row =>
    (!selectedKeyword || row.dataset.keyword.split('|').includes(selectedKeyword)) &&
    (!selectedForum || row.dataset.forum === selectedForum) &&
    (!selectedMonth || row.dataset.month === selectedMonth) &&
    (!selectedNew || row.dataset.new === selectedNew)
  );
  const shown = Math.min(shownCount, matched.length);
  const shownSet = new Set(matched.slice(0, shown));
  detailRows.forEach(row => {{ row.hidden = !shownSet.has(row); }});
  visibleCount.textContent = shown;
  matchedCount.textContent = matched.length;
  loadMoreBtn.hidden = shown >= matched.length;
}}
function bindChips(containerId, onSelect) {{
  const buttons = [...document.querySelectorAll(`#${{containerId}} .filter-chip`)];
  buttons.forEach(button => button.addEventListener('click', () => {{
    buttons.forEach(item => item.classList.remove('active'));
    button.classList.add('active');
    onSelect(button.dataset.value);
    shownCount = PAGE_SIZE;
    applyFilters();
  }}));
}}
bindChips('keywordChips', value => selectedKeyword = value);
bindChips('forumChips', value => selectedForum = value);
bindChips('monthChips', value => selectedMonth = value);
bindChips('newChips', value => selectedNew = value);
loadMoreBtn.addEventListener('click', () => {{
  shownCount += PAGE_SIZE;
  applyFilters();
}});
applyFilters();
</script>
</div></body></html>'''
OUT.write_text(html, encoding='utf-8')
print(
    OUT.resolve(),
    f'rows={len(rows)}',
    f'new={len(new_rows)}',
    f'baseline={previous_report_label}',
    f'bytes={OUT.stat().st_size}',
)
