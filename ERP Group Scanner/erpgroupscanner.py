import requests
import unicodedata
import time
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# Function to normalize fancy fonts to plain text
def normalize_text(text):
    return ''.join(
        char for char in unicodedata.normalize('NFD', text)
        if unicodedata.category(char) != 'Mn'
    ).lower()

# Function to handle swapped characters
def match_with_swaps(group_name, keyword):
    swaps = {
        # Lowercase letters
        'a': ['@', '4', 'α', '∆', 'д', '🅰️', '𝓪', '𝖆', '𝗮', '𝙖', '𝘢', '𝕒', 'Ａ', '𝐀', '🅐'],
        'b': ['8', 'ß', 'в', 'Β', '6', '🅱️', '𝓫', '𝖇', '𝗯', '𝙗', '𝘣', '𝕓', 'Ｂ', '𝐁', '🅑'],
        'c': ['(', '{', '<', '©', '¢', '🌜', '𝓬', '𝖈', '𝗰', '𝙘', '𝘤', '𝕔', 'Ｃ', '𝐂', '🅒'],
        'd': ['|)', 'đ', 'ð', 'Ð', '🌛', '𝓭', '𝖉', '𝗱', '𝙙', '𝘥', '𝕕', 'Ｄ', '𝐃', '🅓'],
        'e': ['3', '€', 'є', 'ξ', '🎗️', '𝓮', '𝖊', '𝗲', '𝙚', '𝘦', '𝕖', 'Ｅ', '𝐄', '🅔'],
        'f': ['ƒ', 'ғ', '🌱', '𝓯', '𝖋', '𝗳', '𝙛', '𝘧', '𝕗', 'Ｆ', '𝐅', '🅕'],
        'g': ['9', '6', 'ɢ', 'ʛ', '🌟', '𝓰', '𝖌', '𝗴', '𝙜', '𝘨', '𝕘', 'Ｇ', '𝐆', '🅖'],
        'h': ['#', 'н', 'Ħ', '♓', '🌞', '𝓱', '𝖍', '𝗵', '𝙝', '𝘩', '𝕙', 'Ｈ', '𝐇', '🅗'],
        'i': ['1', '!', '|', 'ı', 'ι', 'Ϊ', 'ℹ️', '𝓲', '𝖎', '𝗶', '𝙞', '𝘪', '𝕚', 'Ｉ', '𝐈', '🅘'],
        'j': ['ʝ', 'Ĵ', ';', '🌙', '𝓳', '𝖏', '𝗷', '𝙟', '𝘫', '𝕛', 'Ｊ', '𝐉', '🅙'],
        'k': ['κ', '|<', 'Қ', '🎋', '𝓴', '𝖐', '𝗸', '𝙠', '𝘬', '𝕜', 'Ｋ', '𝐊', '🅚'],
        'l': ['1', '|', 'ł', 'ι', '∟', '👢', '𝓵', '𝖑', '𝗹', '𝙡', '𝘭', '𝕝', 'Ｌ', '𝐋', '🅛'],
        'm': ['м', 'ϻ', '♏', '🌊', '𝓶', '𝖒', '𝗺', '𝙢', '𝘮', '𝕞', 'Ｍ', '𝐌', '🅜'],
        'n': ['η', 'и', 'п', 'ñ', '∩', '🎵', '𝓷', '𝖓', '𝗻', '𝙣', '𝘯', '𝕟', 'Ｎ', '𝐍', '🅝'],
        'o': ['0', 'ø', '°', 'ο', 'σ', '○', '🅾️', '🌕', '𝓸', '𝖔', '𝗼', '𝙤', '𝘰', '𝕠', 'Ｏ', '𝐎', '🅞'],
        'p': ['ρ', 'þ', 'ƿ', '🅿️', '𝓹', '𝖕', '𝗽', '𝙥', '𝘱', '𝕡', 'Ｐ', '𝐏', '🅟'],
        'q': ['9', 'զ', 'ԛ', '🌈', '𝓺', '𝖖', '𝗾', '𝙦', '𝘲', '𝕢', 'Ｑ', '𝐐', '🅠'],
        'r': ['я', '®', 'г', '🌹', '𝓻', '𝖗', '𝗿', '𝙧', '𝘳', '𝕣', 'Ｒ', '𝐑', '🅡'],
        's': ['5', '$', '§', 'ş', 'ʃ', '💲', '𝓼', '𝖘', '𝘀', '𝙨', '𝘴', '𝕤', 'Ｓ', '𝐒', '🅢'],
        't': ['7', '+', '†', 'τ', 'ŧ', '✝️', '🌴', '𝓽', '𝖙', '𝘁', '𝙩', '𝘵', '𝕥', 'Ｔ', '𝐓', '🅣'],
        'u': ['υ', 'μ', '∪', 'ц', '🌻', '𝓾', '𝖚', '𝘂', '𝙪', '𝘶', '𝕦', 'Ｕ', '𝐔', '🅤'],
        'v': ['υ', 'ν', '√', '✅', '𝓿', '𝖛', '𝗏', '𝙫', '𝘷', '𝕧', 'Ｖ', '𝐕', '🅥'],
        'w': ['ω', 'ψ', 'vv', '🌊', '𝔀', '𝖜', '𝗐', '𝙬', '𝘸', '𝕨', 'Ｗ', '𝐖', '🅦'],
        'x': ['×', '✗', '✘', 'χ', '❌', '𝔁', '𝖝', '𝗑', '𝙭', '𝘹', '𝕩', 'Ｘ', '𝐗', '🅧'],
        'y': ['¥', 'ү', 'γ', 'ч', '🌼', '𝔂', '𝖞', '𝗒', '𝙮', '𝘺', '𝕪', 'Ｙ', '𝐘', '🅨'],
        'z': ['2', 'ƶ', 'ʐ', 'ζ', '🌟', '𝔃', '𝖟', '𝗓', '𝙯', '𝘻', '𝕫', 'Ｚ', '𝐙', '🅩'],
    
        # Numbers
        '0': ['o', 'O', '°', '○', '🅾️'],
        '1': ['l', 'I', '!', '|', '𝟙', '➊', '１'],
        '2': ['ƻ', 'Ζ', '𝟚', '➋', '２'],
        '3': ['E', 'э', 'Ǝ', '𝟛', '➌', '３'],
        '4': ['A', 'Ᾱ', '𝟜', '➎', '４'],
        '5': ['S', 'Ƨ', '𝟝', '➏', '５'],
        '6': ['G', '6', '𝟞', '➐', '６'],
        '7': ['T', '𝟟', '➑', '７'],
        '8': ['B', '𝟠', '➒', '８'],
        '9': ['P', '𝟡', '➓', '９']
    }

    variations = {keyword}
    for char, replacements in swaps.items():
        new_variations = set()
        for word in variations:
            for replacement in replacements:
                new_variations.add(word.replace(char, replacement))
        variations.update(new_variations)

    return any(variant in group_name for variant in variations)

# Function to check if a group exists and matches keywords
def check_group(group_id, keywords, session):
    url = f"https://groups.roblox.com/v1/groups/{group_id}"
    try:
        response = session.get(url, timeout=30) #if you hit freqent rate limits make sure to change the timeout time, and the sleep time at line 85,
        if response.status_code == 200:
            data = response.json()
            group_name = data.get("name", "")
            normalized_name = normalize_text(group_name)

            for keyword in keywords:
                normalized_keyword = normalize_text(keyword)
                if normalized_keyword in normalized_name or match_with_swaps(normalized_name, normalized_keyword):
                    print(f"Keyword matched: {keyword} in group: {group_name}")
                    return True, group_name
        elif response.status_code == 429:  # Too many requests
            print("Rate limit hit. Waiting...")
            time.sleep(10)
        return False, None
    except requests.exceptions.Timeout:
        print(f"Timeout for group {group_id}. Skipping...")
        return False, None
    except requests.RequestException as e:
        print(f"Error checking group {group_id}: {e}")
        return False, None

# Main function
def scan_groups(keywords, start=17000, end=20000, output_file=r"results.txt"): # you dont need to change numbers here, it will automatically ask for the range
    group_urls = []
    session = requests.Session()
    retries = Retry(total=3, backoff_factor=0.5, status_forcelist=[500, 502, 503, 504])
    session.mount('http://', HTTPAdapter(max_retries=retries))
    session.mount('https://', HTTPAdapter(max_retries=retries))

    request_count = 0  # Track the number of requests made
    with open(output_file, "w", encoding="utf-8") as file:
        for group_id in range(start, end + 1):
            exists, group_name = check_group(group_id, keywords, session)
            request_count += 1

            if exists:
                result = f"https://www.roblox.com/groups/{group_id}/ - Name: {group_name}"
                group_urls.append(result)
                print(f"Found: {result}")
                file.write(result + "\n")

            # Adjust sleep dynamically to avoid rate limits
            if request_count % 100 == 0:  # After every 100 requests
                print(f"Processed {request_count} requests. Pausing briefly to avoid rate limits.")
                time.sleep(2)  # Pause briefly to prevent server overload, increase it if frequent rate limit persists
            else:
                time.sleep(3)  # Regular 200ms delay change it if frequent rate limit persists

    return group_urls

# Input from user
print("Enter keywords separated by commas:")
keywords = input().strip().split(",")
print("It is wiser to set a small range of scan length to avoid rate limits and timeouts!") 
print("Enter start group ID (e.g., 10000):") 
start_id = int(input().strip())

print("Enter end group ID (e.g., 20000):")
end_id = int(input().strip())

print("Enter the full path to the output file (e.g., C:\\path\\to\\results.txt):")
output_file = input().strip()

print("Scanning groups...")
results = scan_groups(keywords, start=start_id, end=end_id, output_file=output_file)

if results:
    print(f"\nFinished scanning. Matching groups saved to: {output_file}")
else:
    print("No matching groups found.")


#keywords for copy and paste
#qoh,queen of hearts,doll,barbie,spade,adult,fard,fart,gassy,world,roleplay,server,cutie,cute,gas,rp,sinner,sin,godless,god,seat,temple,spades,freaky,studio,caramella,fan,girls,boys,cloud,slob,feet,fetish,raceplay,stinky,inch,girthy,homeless,slob,homo,erectus,ass,fat,chubby,kkk,ku klux klan,nazi,third reich,reich,the reich,club,cute,cutie,sub,submissive,futa,poop,toilet,shit,cramp,feces,big,carrot,diaper,abdl,wet,cupid,cupidity,cupidities,inbreed,furry,lgbtq,lgbtqia,queen of, king of, paws,q_s,vibe,vibing,bimbo,black lives matter,blm,toy,closet,superior,gals,trash,trashy,sophisticated,bunny,shop,shopx,ace,aced,clothes,abc,abcs,aced,yih,hangout,magic,store,fembox,femxboy,miso,cruel,curses,thumper,inflate,inflatable,mistakes,mistake,warning,rot,root,purity,pink,pinky,my,friends,friendds,lab,las,latex,dream,bull,kitty,skin,moist,mama,papa,doll,plague,paradox,onyx,tiger,top,nom,boobs,boob
# you can add word filters here, by putting a , in between them, the script scans like this: if there is a word in the keyword input of the group, it gets printed out

#Created by BenXiadous aka Bencehhh