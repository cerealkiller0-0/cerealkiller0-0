"""Builds the pixel weather window (5 seamless SVG slices) for a GitHub profile.
Run:  python build.py            -> fetches live Dhaka weather (Open-Meteo, no API key)
      python build.py --sample   -> uses sample data (offline preview)"""
import sys, json, math, random, urllib.request

NAVY, PINK, BLUE, WHITE = "#1a1060", "#fbb4ec", "#8fa3ee", "#ffe8fb"
W, H = 800, 400
LEFT_W, BTN_W = 340, 115
F = {'<':"...#.|..#..|.#...|..#..|...#.",
'A':".###.|#...#|#####|#...#|#...#",'B':"####.|#...#|####.|#...#|####.",'C':".####|#....|#....|#....|.####",
'D':"####.|#...#|#...#|#...#|####.",'E':"#####|#....|####.|#....|#####",'F':"#####|#....|####.|#....|#....",
'G':".####|#....|#..##|#...#|.###.",'H':"#...#|#...#|#####|#...#|#...#",'I':"#####|..#..|..#..|..#..|#####",
'K':"#...#|#..#.|###..|#..#.|#...#",'L':"#....|#....|#....|#....|#####",'M':"#...#|##.##|#.#.#|#...#|#...#",
'N':"#...#|##..#|#.#.#|#..##|#...#",'O':".###.|#...#|#...#|#...#|.###.",'P':"####.|#...#|####.|#....|#....",
'R':"####.|#...#|####.|#..#.|#...#",'S':".####|#....|.###.|....#|####.",'T':"#####|..#..|..#..|..#..|..#..",
'U':"#...#|#...#|#...#|#...#|.###.",'W':"#...#|#...#|#.#.#|##.##|#...#",'Y':"#...#|.#.#.|..#..|..#..|..#..",
'V':"#...#|#...#|#...#|.#.#.|..#..",'X':"#...#|.#.#.|..#..|.#.#.|#...#",
'0':".###.|#..##|#.#.#|##..#|.###.",'1':"..#..|.##..|..#..|..#..|.###.",'2':".###.|#...#|..##.|.#...|#####",
'3':"####.|....#|.###.|....#|####.",'4':"#..#.|#..#.|#####|...#.|...#.",'5':"#####|#....|####.|....#|####.",
'6':".###.|#....|####.|#...#|.###.",'7':"#####|...#.|..#..|.#...|.#...",'8':".###.|#...#|.###.|#...#|.###.",
'9':".###.|#...#|.####|....#|.###.",'.':".....|.....|.....|.....|..#..",'%':"#...#|...#.|..#..|.#...|#...#",
'/':"....#|...#.|..#..|.#...|#....",'-':".....|.....|.###.|.....|.....",' ':".....|.....|.....|.....|....."}
def tw(t,u): return len(t)*6*u-u
def text(t,x,y,u,col,anchor="l"):
    if anchor=="c": x-=tw(t,u)/2
    d=[]
    for i,ch in enumerate(t):
        for r,row in enumerate(F[ch].split("|")):
            for c,v in enumerate(row):
                if v=="#": d.append(f"M{x+(i*6+c)*u:.0f} {y+r*u}h{u}v{u}h-{u}z")
    return f'<path d="{"".join(d)}" fill="{col}"/>'
def grid(cells,ox,oy,s):
    return "".join(f'<rect x="{ox+x*s}" y="{oy+y*s}" width="{s}" height="{s}" fill="{c}"/>' for (x,y),c in cells.items())
def circ(cx,cy,r): return {(x,y) for x in range(16) for y in range(16) if (x+.5-cx)**2+(y+.5-cy)**2<=r*r}
def sun(cx=8,cy=8,r=3.6,rays=True):
    c={p:PINK for p in circ(cx,cy,r)}
    for p in list(c):
        if p[0]<=cx-1 and p[1]<=cy-1: c[p]=WHITE
    if rays:
        for a in range(8):
            for dist in (r+1.6,r+2.6):
                x=round(cx-.5+math.cos(a*math.pi/4)*dist); y=round(cy-.5+math.sin(a*math.pi/4)*dist)
                if 0<=x<16 and 0<=y<16: c[(x,y)]=PINK
    return c
def cloud(dx=0,dy=0):
    s=circ(5,7,3)|circ(9,5.2,3.6)|circ(12.2,7.6,2.8)|{(x,y) for x in range(2,15) for y in range(8,11)}
    s={(x+dx,y+dy) for x,y in s}; ymax=max(y for _,y in s)
    return {p:(BLUE if p[1]>=ymax-1 else WHITE) for p in s}
def moon():
    a=circ(8,8,5.5); b=circ(11,6.4,4.8)
    return {p:PINK for p in a-b}
def scene(code,day):
    """returns (static pixels, animated-drop pixels, label)"""
    if code==0: return (sun() if day else moon()),{}, "CLEAR"
    if code in(1,2):
        c=sun(5,5,2.6) if day else moon(); c.update(cloud(1,4)); return c,{}, "PARTLY CLOUDY" if False else "CLOUDY"
    if code in(3,): return cloud(0,2),{}, "CLOUDY"
    if code in(45,48): return cloud(0,2),{(x,12):BLUE for x in (3,6,9,12)},"FOG"
    if code in(71,73,75,77,85,86): return cloud(0,0),{(x,y):WHITE for x,y in ((4,12),(7,13),(10,12),(13,13))},"SNOW"
    if code>=95: 
        bolt={(8,11):PINK,(7,12):PINK,(8,12):PINK,(6,13):PINK,(7,13):PINK,(8,14):PINK}
        return {**cloud(0,-1),**bolt},{},"STORM"
    return cloud(0,-1),{(x,12):BLUE for x in (4,7,10,13)},"RAIN"
def star(x,y,cls,big=False):
    return grid({(0,0):WHITE,(1,0):PINK} if False else ({(1,0):WHITE,(0,1):WHITE,(1,1):WHITE,(2,1):WHITE,(1,2):WHITE} if big else {(0,0):WHITE}),x,y,4 if big else 5).replace("<rect",f'<rect class="{cls}"')
def heart(x,y,s=1):
    return f'<path transform="translate({x} {y}) scale({s})" d="M0 5C-11 -3 -8 -13 0 -7C8 -13 11 -3 0 5Z" fill="{PINK}" stroke="{NAVY}" stroke-width="3" stroke-linejoin="round"/>'
def spark(x,y,s=1):
    return f'<path transform="translate({x} {y}) scale({s})" d="M0 -8L2.5 -2.5L8 0L2.5 2.5L0 8L-2.5 2.5L-8 0L-2.5 -2.5Z" fill="{WHITE}" stroke="{NAVY}" stroke-width="2.5" stroke-linejoin="round"/>'
def icon(name):
    o=f'stroke="{NAVY}" stroke-width="4" stroke-linejoin="round" stroke-linecap="round"'
    if name=="facebook":
        b=f'<rect x="-38" y="-38" width="76" height="76" rx="20" fill="#8db4ff" {o}/><path d="M7 42V-8Q7 -24 24 -21M-6 6H22" fill="none" stroke="{WHITE}" stroke-width="10" stroke-linecap="round"/>'
    elif name=="instagram":
        b=(f'<defs><linearGradient id="ig" x1="0" y1="1" x2="1" y2="0"><stop offset="0" stop-color="#ffd59a"/><stop offset=".5" stop-color="#ff9fcf"/><stop offset="1" stop-color="#b9a4ff"/></linearGradient></defs>'
           f'<rect x="-38" y="-38" width="76" height="76" rx="22" fill="url(#ig)" {o}/><circle r="16" fill="none" stroke="{WHITE}" stroke-width="6"/><circle cx="20" cy="-20" r="4.5" fill="{WHITE}"/>')
    elif name=="discord":
        b=(f'<path d="M-36 -18Q-36 -34 -20 -34H20Q36 -34 36 -18V16Q36 32 20 32H-4L-12 42L-20 32Q-36 32 -36 16Z" fill="#b8aaff" {o}/>'
           f'<ellipse cx="-14" cy="-1" rx="8" ry="10" fill="{WHITE}"/><ellipse cx="14" cy="-1" rx="8" ry="10" fill="{WHITE}"/><circle cx="-13" cy="1" r="3.5" fill="{NAVY}"/><circle cx="15" cy="1" r="3.5" fill="{NAVY}"/>')
    else:
        b=(f'<rect x="-38" y="-38" width="76" height="76" rx="20" fill="#8fd0ff" {o}/><circle cx="-19" cy="-17" r="6.5" fill="{WHITE}"/>'
           f'<path d="M-19 -6V28M-3 28V-6M-3 8Q-1 -6 14 -5Q28 -4 28 12V28" fill="none" stroke="{WHITE}" stroke-width="10" stroke-linecap="round" stroke-linejoin="round"/>')
    return b+heart(36,-36,.9)+spark(-40,32,.9)

def static(w):
    s=[f'<rect width="{W}" height="{H}" fill="{NAVY}"/><rect x="6" y="6" width="{W-12}" height="{H-12}" fill="{PINK}"/>',
       f'<rect x="6" y="60" width="{W-12}" height="4" fill="{NAVY}"/>',
       f'<rect x="18" y="76" width="{W-36}" height="310" fill="{NAVY}"/><rect x="24" y="82" width="{W-48}" height="298" fill="{BLUE}"/>']
    for x in (24,60,96): s.append(f'<rect x="{x}" y="20" width="26" height="26" fill="{NAVY}"/><rect x="{x+6}" y="26" width="14" height="14" fill="{WHITE}"/><rect x="{x+14}" y="32" width="6" height="8" fill="{BLUE}"/>')
    s.append(text("WEATHER.APP",146,23,4,NAVY)); s.append(text("CEREALKILLER<3",449,26,3,BLUE))
    for i in range(3): s.append(f'<rect x="748" y="{22+i*10}" width="34" height="5" fill="{NAVY}"/>')
    s.append(f'<path d="M708 22h22v22h-6v-8l-10 10-6-6 10-10h-10z" fill="{NAVY}"/>')
    s.append(text("FIND ME ON",560,110,5,NAVY,"c"))
    for i,l in enumerate(("FB","IG","DC","IN")): s.append(text(l,LEFT_W+BTN_W*i+BTN_W//2,292,3,NAVY,"c"))
    s.append(f'<rect x="388" y="344" width="384" height="5" fill="{NAVY}"/><circle cx="388" cy="346" r="12" fill="{NAVY}"/><circle cx="388" cy="346" r="6" fill="{PINK}"/>')
    s.append(heart(770,100,1.1)); s.append(spark(366,92,1.1))
    return "".join(s)
CSS=("<style>@keyframes bob{0%,100%{transform:translateY(0)}50%{transform:translateY(-8px)}}"
"@keyframes tw{0%,100%{opacity:1}50%{opacity:.15}}@keyframes fall{0%{transform:translateY(-10px);opacity:0}30%{opacity:1}100%{transform:translateY(40px);opacity:0}}"
"@keyframes bl{0%,60%{opacity:1}61%,100%{opacity:0}}"
".bob{animation:bob 2.4s ease-in-out infinite}.a{animation:tw 2s steps(2) infinite}.b{animation:tw 3s steps(2) infinite .7s}.c{animation:tw 2.5s steps(2) infinite 1.3s}"
".drop{animation:fall 1.4s steps(5) infinite}.d2{animation-delay:.35s}.d3{animation-delay:.7s}.d4{animation-delay:1.05s}</style>")
def svg(x0,w,body,label):
    return f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{H}" viewBox="{x0} 0 {w} {H}" role="img" aria-label="{label}">{CSS}{static(w)}{body}</svg>'
def left(d):
    code,temp,hum,wind,day=d
    st,drops,word=scene(code,day)
    px,py=36,94
    o=[f'<rect x="{px}" y="{py}" width="280" height="274" fill="{NAVY}"/><rect x="{px+8}" y="{py+8}" width="264" height="258" fill="none" stroke="{BLUE}" stroke-width="4"/>']
    rnd=random.Random(3)
    for i in range(16):
        x,y=px+16+rnd.randrange(0,248,4),py+16+rnd.randrange(0,60,4)
        o.append(star(x,y,("a","b","c")[i%3],i%5==0))
    o.append(f'<g class="bob">{grid(st,112,108,8)}</g>')
    for i,(p,c) in enumerate(drops.items()):
        o.append(f'<g class="drop d{i%4+1}">{grid({p:c},112,108,8)}</g>'.replace('class="drop d1"','class="drop"'))
    cx=px+140
    o.append(text(f"{temp}C",cx,246,6,PINK,"c")); o.append(text(word,cx,286,4,WHITE,"c"))
    o.append(text(f"HUMID {hum}%",cx,318,3,BLUE,"c")); o.append(text(f"WIND {wind} KM/H",cx,340,3,BLUE,"c"))
    return svg(0,LEFT_W,"".join(o),f"Dhaka weather: {temp} degrees C, {word}, humidity {hum}%, wind {wind} km/h")
def button(i,name):
    cx=LEFT_W+BTN_W*i+BTN_W/2
    body=f'<g transform="translate({cx} 228)"><g class="bob" style="animation-delay:{i*0.3}s">{icon(name)}</g></g>'
    return svg(LEFT_W+BTN_W*i,BTN_W,body,name)
def fetch():
    u=("https://api.open-meteo.com/v1/forecast?latitude=23.8103&longitude=90.4125"
       "&current=temperature_2m,relative_humidity_2m,weather_code,wind_speed_10m,is_day&timezone=Asia%2FDhaka")
    c=json.load(urllib.request.urlopen(u,timeout=20))["current"]
    return (int(c["weather_code"]),round(c["temperature_2m"]),round(c["relative_humidity_2m"]),round(c["wind_speed_10m"]),bool(c["is_day"]))
if __name__=="__main__":
    d=(2,31,78,12,True) if "--sample" in sys.argv else fetch()
    open("assets/weather-left.svg","w").write(left(d))
    for i,n in enumerate(("facebook","instagram","discord","linkedin")): open(f"assets/btn-{n}.svg","w").write(button(i,n))
    print("built",d)
