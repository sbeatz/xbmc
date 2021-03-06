#!/usr/bin/env python
# -*- coding: utf-8 -*-
import time
import subprocess
import common
import random

from BeautifulSoup import BeautifulStoneSoup
from BeautifulSoup import BeautifulSoup

try:
    from xml.etree import ElementTree
except:
    from elementtree import ElementTree
    
pluginhandle = common.pluginhandle
xbmc = common.xbmc
xbmcplugin = common.xbmcplugin
urllib = common.urllib
sys = common.sys
xbmcgui = common.xbmcgui
re = common.re
demjson = common.demjson
settings = common.addon
os = common.os
hashlib = common.hashlib

userinput = os.path.join(common.pluginpath, 'tools', 'userinput.exe' )
waitsec = int(settings.getSetting("clickwait")) * 1000
pin = settings.getSetting("pin")
waitpin = int(settings.getSetting("waitpin")) * 1000
osLinux = xbmc.getCondVisibility('system.platform.linux')
osOsx = xbmc.getCondVisibility('system.platform.osx')
osWin = xbmc.getCondVisibility('system.platform.windows')
screenWidth = int(xbmc.getInfoLabel('System.ScreenWidth'))
screenHeight = int(xbmc.getInfoLabel('System.ScreenHeight'))
playPlugin = ['','plugin.program.browser.launcher', 'plugin.program.chrome.launcher']
selPlugin = playPlugin[int(settings.getSetting("playmethod"))]
trailer = common.args.trailer
selbitrate = common.args.selbitrate
isAdult = int(common.args.adult)
amazonUrl = common.BASE_URL + "/dp/" + common.args.asin
Dialog = xbmcgui.Dialog()

def PLAYVIDEO():
    global amazonUrl
    if trailer == '1':
        if selPlugin == '':
            PLAYTRAILER()
            return
        amazonUrl += "/?autoplaytrailer=1"
    else:
        if selPlugin == '':
            PLAYVIDEOINT()
            return
        amazonUrl += "/?autoplay=1"
    kiosk = 'yes'
    if settings.getSetting("kiosk") == 'false': kiosk = 'no'
    
    url = 'plugin://%s/?url=%s&mode=showSite&kiosk=%s' % (selPlugin, urllib.quote_plus(amazonUrl), kiosk)
    common.Log('Run plugin: %s' % url)
    xbmc.executebuiltin('RunPlugin(%s)' % url)

    if settings.getSetting("fullscreen") == 'true':
        pininput = 0
        if settings.getSetting("pininput") == 'true': pininput = 1
        input(mousex=-1,mousey=350)
        if isAdult == 1 and pininput == 1:
            xbmc.sleep(int(waitsec*0.75))
            input(keys=pin)
            xbmc.sleep(waitpin)
        else:
            xbmc.sleep(waitsec)
        if isAdult == 0: pininput = 1
        if pininput == 1:
            input(mousex=-1,mousey=350,click=2)
            xbmc.sleep(500)
            #input(mousex=9999,mousey=0)

def input(mousex=0,mousey=0,click=0,keys=False,delay='200'):
    if mousex == -1: mousex = screenWidth/2
    if mousey == -1: mousey = screenHeight/2

    if osWin:
        app = userinput
        mouse = ' mouse %s %s' % (mousex,mousey)
        mclk = ' ' + str(click)
        keybd = ' key %s{Enter} %s' % (keys,delay)
    elif osLinux:
        app = 'xdotool'
        mouse = ' mousemove %s %s' % (mousex,mousey)
        mclk = ' click --repeat %s 1' % click
        keybd = ' type --delay %s %s && xdotool key Return' % (delay, keys)
    elif osOsx:
        app = 'cliclick'
        mouse = ' m:'
        if click == 1: mouse = ' c:'
        elif click == 2: mouse = ' dc:'
        mouse += '%s,%s' % (mousex,mousey)
        mclk = ''
        keybd = ' -w %s t:%s kp:return' % (delay, keys)

    if keys:
        cmd = app + keybd
    else:
        cmd = app + mouse
        if click: cmd += mclk
    common.Log('Run command: %s' % cmd)
    subprocess.Popen(cmd, shell=True)

def GETSUBTITLES(suc, data):
    if not suc: return 'false'
    subtitleLanguages = data['subtitles']['content']['languages']
    if len(subtitleLanguages) > 0:
        subtitleUrl = subtitleLanguages[0]['url']
        subtitles = CONVERTSUBTITLES(subtitleUrl)
        common.SaveFile(os.path.join(common.pldatapath,values['asin']+'.srt'), subtitles)
        return 'true'
    return 'false'
        
def CONVERTSUBTITLES(url):
    xml=common.getURL(url)
    tree = BeautifulStoneSoup(xml, convertEntities=BeautifulStoneSoup.XML_ENTITIES)
    lines = tree.find('tt:body').findAll('tt:p')
    stripTags = re.compile(r'<.*?>',re.DOTALL)
    spaces = re.compile(r'\s\s\s+')
    srt_output = ''
    count = 1
    displaycount = 1
    for line in lines:
        sub = line.renderContents()
        sub = stripTags.sub(' ', sub)
        sub = spaces.sub(' ', sub)
        sub = sub.decode('utf-8')
        start = line['begin'].replace('.',',')
        if count < len(lines):
            end = line['end'].replace('.',',')
        line = str(displaycount)+"\n"+start+" --> "+end+"\n"+sub+"\n\n"
        srt_output += line
        count += 1
        displaycount += 1
    return srt_output.encode('utf-8')

def SETSUBTITLES(asin):
    subtitles = os.path.join(common.pldatapath, asin+'.srt')
    if os.path.isfile(subtitles) and xbmc.Player().isPlaying():
        common.Log('Subtitles Enabled.')
        xbmc.Player().setSubtitles(subtitles)
    elif xbmc.Player().isPlaying():
        common.Log('No Subtitles File Available.')
    else:
        common.Log('No Media Playing. Subtitles Not Assigned.')

def GETTRAILERS(suc, rtmpdata):
    if suc:
        sessionId = rtmpdata['streamingURLInfoSet']['sessionId']
        cdn = rtmpdata['streamingURLInfoSet']['cdn']
        rtmpurls = rtmpdata['streamingURLInfoSet']['streamingURLInfo']
        title = rtmpdata['metadata']['title'].replace('[HD]','')
        return rtmpurls, sessionId, cdn, title
    else:
        return False, False, False, rtmpdata

def PLAYTRAILER():
    values = GETFLASHVARS(amazonUrl) 
    if not values:        
        return

    rtmpurls, streamSessionID, cdn, videoname = GETTRAILERS(*getUrldata('catalog/GetStreamingTrailerUrls', values))
    if not rtmpurls:
        Dialog.ok('No Trailer available','')
    else:
        PLAY(rtmpurls, values, Trailer=True, title=videoname)
        
def GETSTREAMS(suc, rtmpdata):
    if not suc:
        return False, False, False, rtmpdata
    drm = rtmpdata['urlSets']['streamingURLInfoSet'][0]['drm']
    if drm <> 'NONE':
        Dialog.ok('DRM Detected','This video uses %s DRM' % drm)

    sessionId = rtmpdata['urlSets']['streamingURLInfoSet'][0]['sessionId']
    cdn = rtmpdata['urlSets']['streamingURLInfoSet'][0]['cdn']
    rtmpurls = rtmpdata['urlSets']['streamingURLInfoSet'][0]['streamingURLInfo']
    title = rtmpdata['metadata']['title'].replace('[HD]','')
    return rtmpurls, sessionId, cdn, title
    
def GETLANG(suc, rtmpdata):
    if not suc:
        return False, rtmpdata
    langid = []
    langname = []
    try:
        format = rtmpdata['titles'][0]['formats'][0]
        for lang in format['audioTrackLanguageList']['audioTrackLanguage'][0]['audioLanguageList']['audioLanguage']:
            langid.append(lang['audioFormatAssetList']['audioFormatAsset'][0]['audioTrackId'])
            langname.append(lang['language']['displayName'])
    except:
        langname.append(common.getString(30209))
        langid.append('')
    lang = Dialog.select(common.getString(30115), langname)
    if lang > -1:
        return True, '&audioTrackId=' + langid[lang]
    return False, False
        
def PLAYVIDEOINT():
    audioid = ''
    values = GETFLASHVARS(amazonUrl)
    if not values:        
        return
    values['subtitle'] = 'false'
    if selbitrate == 'org':
        suc, audioid = GETLANG(*getUrldata('catalog/GetASINDetails', values, devicetypeid='A1MPSLFC7L5AFK', asinlist=True, opt='&NumberOfResults=1', version=2))
        if not suc:
            return
    if common.addon.getSetting("enable_captions")=='true':
        values['subtitle'] = GETSUBTITLES(*getUrldata('catalog/GetSubtitleUrls', values, opt='&NumberOfResults=1&videoType=content'))
    
    rtmpurls, values['streamSessionID'], values['cdn'], title = GETSTREAMS(*getUrldata('catalog/GetStreamingUrlSets', values, opt=audioid))
    if not rtmpurls:
        Dialog.notification(common.getString(30203), title, xbmcgui.NOTIFICATION_ERROR)
        return
    values = PLAY(rtmpurls, values, title=title)
    if not values: return

    if common.addon.getSetting("enable_captions")=='true':
        while not xbmc.Player().isPlaying(): xbmc.sleep(100)
        SETSUBTITLES(values['asin'])
    """
    print getUrldata('usage/ReportStartStreamEvent', values, extra=True)
    while xbmc.Player().isPlaying(): xbmc.sleep(1000)
    print getUrldata('usage/ReportStopStreamEvent', values, extra=True)
    """
        
def GETFLASHVARS(pageurl):
    cookie = common.mechanizeLogin()
    showpage = common.getURL(pageurl, useCookie=cookie)
    common.WriteLog(showpage, 'flashvars', 'w')
    if not showpage:
        Dialog.notification(common.__plugin__, Error('CDP.InvalidRequest'), xbmcgui.NOTIFICATION_ERROR)
        return False
    values = {}
    search = {'asin'       : '"pageAsin":"(.*?)"',
              'sessionID'  : "ue_sid='(.*?)'",
              'marketplace': "ue_mid='(.*?)'",
              'customer'   : '"customerID":"(.*?)"'}
    if 'var config' in showpage:
        flashVars = re.compile('var config = (.*?);',re.DOTALL).findall(showpage)
        flashVars = demjson.decode(unicode(flashVars[0], errors='ignore'))
        values = flashVars['player']['fl_config']['initParams']
        swfUrl = flashVars['player']['fl_config']['playerSwf']
    else:
        for key, pattern in search.items():
            result = re.compile(pattern, re.DOTALL).findall(showpage)
            if result: values[key] = result[0]
        values['swfUrl'] = 'http://ecx.images-amazon.com/images/G/01/digital/video/webplayer/1.0.379.0/swf/UnboxScreeningRoomClient.swf'
    
    for key in values.keys():
        if not values.has_key(key):
            Dialog.notification(common.getString(30200), common.getString(30210), xbmcgui.NOTIFICATION_ERROR)
            return False

    values['deviceTypeID']  = 'A324MFXUEZFF7B' #Sony GoogleTV unenc Flash
    #values['deviceTypeID']  = 'A13Q6A55DBZB7M' #enc Flash
    #values['deviceTypeID']  = 'A35LWR0L7KC0TJ' #Logitech GoogleTV unenc Flash
    #values['deviceTypeID']  = 'A63V4FRV3YUP9' #enc Silverlight
    values['userAgent']     = "GoogleTV 162671"
    values['deviceID']      = common.hmac.new(common.UserAgent, common.gen_id(), hashlib.sha224).hexdigest()
    rand = 'onWebToken_' + str(random.randint(0,484))
    pltoken = common.getURL(common.BASE_URL + "/gp/video/streaming/player-token.json?callback=" + rand, useCookie=cookie)
    try:
        values['token']  = re.compile('"([^"]*).*"([^"]*)"').findall(pltoken)[0][1]
    except:
        Dialog.notification(common.getString(30200), common.getString(30201), xbmcgui.NOTIFICATION_ERROR)
        return False
    return values
    
def PLAY(rtmpurls,values,Trailer=False,title=False):
    lbitrate = int(settings.getSetting("bitrate"))
    if selbitrate == '1':
        lbitrate = -1
    mbitrate = 0
    streams = []
    for data in rtmpurls:
        url = data['url']
        bitrate = float(data['bitrate'])
        videoquality = data['contentQuality']
        audioquality = data['audioCodec']
        try:
            formatsplit = re.compile("_video_([^_]*)_.*_audio_([^_]*)_([0-9a-zA-Z]*)").findall(url)
            videoquality += ' ' + formatsplit[0][0]
            audioquality += ' ' + formatsplit[0][2]
        except: pass
        if lbitrate <= 0:
            streams.append([bitrate,url,videoquality,audioquality])
        elif bitrate >= mbitrate and bitrate <= lbitrate:
            mbitrate = bitrate
            rtmpurl = url

    if lbitrate <= 0:
        streamsout = []
        for stream in streams:
            if stream[0] > 999: 
                streamsout.append(str(stream[0]/1000)+' Mbps - '+stream[2]+', '+stream[3])
            else: 
                streamsout.append(str(int(stream[0]))+' Kbps - '+stream[2]+', '+stream[3])
        quality = Dialog.select(common.getString(30114), streamsout)
        if quality!=-1:
            mbitrate = streams[quality][0]
            rtmpurl = streams[quality][1]
        else:
            return False

    values['streamurl'] = rtmpurl
    values['bitrate'] = str(mbitrate)
    rtmpurlSplit = re.compile("([^:]*):\/\/([^\/]+)\/([^\/]+)\/([^\?]+)(\?.*)?").findall(rtmpurl)[0]
    protocol = rtmpurlSplit[0]
    hostname = rtmpurlSplit[1]
    appName =  rtmpurlSplit[2]
    stream = rtmpurlSplit[3]#.replace('de$de','de')#.replace('$','\x5c24')
    auth = rtmpurlSplit[4]
    tcurl = protocol[0:-1] + '://' + hostname + '/' + appName
    #hostname = getIP(hostname) + ':1935'
    basertmp = protocol[0:-1] + '://' + hostname + '/' + appName
    if 'edgefcs' in hostname:
        basertmp += auth
    else:
        stream += auth

    finalUrl = '%s app=%s swfUrl=%s pageUrl=%s playpath=%s tcUrl=%s swfVfy=true' % (basertmp, appName, values['swfUrl'], amazonUrl, stream, tcurl)
    infoLabels = GetStreamInfo(common.args.asin, title)
    common.WriteLog('Content: %s\nRTMPUrl: %s' %(title,finalUrl), 'content')
    if '$' in stream:
        Dialog.notification(common.getString(30198), title, xbmcgui.NOTIFICATION_ERROR)
        return False
    if Trailer:
        infoLabels['Title'] += ' (Trailer)'
    item = xbmcgui.ListItem(path=finalUrl, thumbnailImage=infoLabels['Thumb'])
    item.setProperty('fanart_image', infoLabels['Fanart'])
    item.setInfo(type="Video", infoLabels=infoLabels)
    if Trailer or selbitrate != '0':
        item.setProperty('IsPlayable', 'true')
        xbmc.Player().play(finalUrl, item)
    else:
        xbmcplugin.setResolvedUrl(pluginhandle, True, item)
    return values

def GetStreamInfo(asin, finalname):
    import movies
    import listmovie
    import tv
    import listtv
    moviedata = movies.lookupMoviedb(asin)
    if moviedata:
        return listmovie.ADD_MOVIE_ITEM(moviedata, onlyinfo=True)
    else:
        epidata = tv.lookupTVdb(asin)
        if epidata:
            return listtv.ADD_EPISODE_ITEM(epidata, onlyinfo=True)
    return {'Title': finalname}
    
def getUrldata(mode, values, format='json', asinlist=False, devicetypeid=False, version=1, firmware='WIN%2017,0,0,134%20PlugIn', opt='', extra=False, useCookie=False):
    if not devicetypeid:
        devicetypeid = values['deviceTypeID']
    url  = common.ATV_URL + '/cdp/' + mode
    url += '?asin=' + values['asin']
    url += '&deviceTypeID=' + devicetypeid
    url += '&firmware=' + firmware
    url += '&customerID=' + values['customer']
    url += '&deviceID=' + values['deviceID']
    url += '&marketplaceID=' + values['marketplace']
    url += '&token=' + values['token']
    url += '&format=' + format
    url += '&version=' + str(version)
    url += '&xws-fa-ov=false'
    url += opt
    if asinlist:
        url = url.replace('?asin=', '?asinlist=')
    if extra:
        url += '&to_timecode=0'
        url += '&start_state=Video'
        url += '&offer_type=SUBSCRIPTION'
        url += '&cdn=' + values['cdn']
        url += '&streaming_session_id=' + values['streamSessionID']
        url += '&download_bandwidth=99999'
        url += '&source_system=' + common.BASE_URL
        url += '&is_timed_text_available=' + values['subtitle']
        url += '&http_referer=ecx.images-amazon.com'
        url += '&from_mode=purchased'
        url += '&event_timestamp=' + str(int(float(time.time()*1000)))
        url += '&url=' + urllib.quote_plus(values['streamurl'])
        url += '&encrypted_customer_id=' + values['customer']
        url += '&device_type_id=' + values['deviceTypeID']
        url += '&bitrate=' + values['bitrate']
        url += '&from_timecode=0'
        url += '&browser=' + urllib.quote_plus(values['userAgent'])
        url += '&client_version=' + values['swfUrl'].split('/')[-3]
        url += '&flash_version=' + firmware
    data = common.getURL(url, common.ATV_URL.split('//')[1], useCookie=useCookie)
    if data:
        jsondata = demjson.decode(data)
        del data
        if jsondata['message']['statusCode'] != "SUCCESS":
            return False, Error(jsondata['message']['body']['code'])
        return True, jsondata['message']['body']
    return False, 'HTTP Fehler'
    
def getIP(url):
    identurl = 'http://'+url+'/fcs/ident'
    ident = common.getURL(identurl)
    ip = re.compile('<fcs><ip>(.+?)</ip></fcs>').findall(ident)[0]
    return ip

def Error(code):
    common.Log(code, xbmc.LOGERROR)
    if 'CDP.InvalidRequest' in code:
        return common.getString(30204)
    elif 'CDP.Playback.NoAvailableStreams' in code:
        return common.getString(30205)
    elif 'CDP.Playback.NotOwned' in code:
        return common.getString(30206)
    elif 'CDP.Authorization.InvalidGeoIP' in code:
        return common.getString(30207)
    elif 'CDP.Playback.TemporarilyUnavailable' in code:
        return common.getString(30208)
    else:
        return common.getString(30209) + ': ' + code