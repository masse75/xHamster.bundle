import re, time, random

NAME = 'xHamster'
randomArt = random.randint(1,3)
ART = 'artwork-'+str(randomArt)+'.jpg'
ICON = 'icon-default.png'
ICON_PREFS  = 'icon-prefs.png'

XH_BASE = 'http://xhamster.com'
XH_CHANNELS = 'http://xhamster.com/channels.php'
XH_CHANNEL = 'http://xhamster.com/channels/%s-%s-%s.html'
XH_LATEST = 'http://xhamster.com/last50.php'
XH_TOPRATED = 'http://xhamster.com/rankings/%s-top-videos.html'
XH_MOSTVIEWED = 'http://xhamster.com/rankings/%s-top-viewed.html'
XH_SEARCH = 'http://xhamster.com/search.php?q=%s&page=%s&content=%s'
XH_PLAYER = 'http://xhcdn.com/key='

USER_AGENT = 'Mozilla/5.0 (Macintosh; U; Intel Mac OS X 10.6; en-US; rv:1.9.2.12) Gecko/20101026 Firefox/3.6.12'


####################################################################################################

def Start():
	Plugin.AddPrefixHandler('/video/xhamster', MainMenu, NAME, ICON, ART)
	Plugin.AddViewGroup('List', viewMode='List', mediaType='items')
	Plugin.AddViewGroup('InfoList', viewMode='InfoList', mediaType='items')
	Plugin.AddViewGroup('PanelStream', viewMode='PanelStream', mediaType='items')

	MediaContainer.title1 = NAME
	MediaContainer.art = R(ART)

	DirectoryItem.thumb = R(ICON)
	VideoItem.thumb = R(ICON)

	HTTP.CacheTime = 0
	HTTP.Headers['User-Agent'] = USER_AGENT


####################################################################################################

def Thumb(url):
	try:
		data = HTTP.Request(url).content
		return DataObject(data, 'image/jpeg')
	except:
		return Redirect(R(ICON))

def channelThumb(url):
	try:
		data = HTTP.Request(url, cacheTime=CACHE_1WEEK).content
		return DataObject(data, 'image/jpeg')
	except:
		return Redirect(R(ICON))

def GetDurationFromString(duration):
	try:
		durationArray = duration.split(":")
		if len(durationArray) == 3:
			hours = int(durationArray[0])
			minutes = int(durationArray[1])
			seconds = int(durationArray[2])
		elif len(durationArray) == 2:
			hours = 0
			minutes = int(durationArray[0])
			seconds = int(durationArray[1])
		elif len(durationArray)	==	1:
			hours = 0
			minutes = 0
			seconds = int(durationArray[0])
		return int(((hours)*3600 + (minutes*60) + seconds)*1000)
	except:
		return 0


####################################################################################################

def MainMenu():
	dir = MediaContainer()
	dir.Append(Function(DirectoryItem(ChannelsMenu, L('Channels'))))
	dir.Append(Function(DirectoryItem(MovieList, L('Newest Videos')), url=XH_LATEST, mainTitle='Newest Videos', pageFormat='latest'))
	dir.Append(Function(DirectoryItem(MovieSort, L('Top Rated')), url=XH_TOPRATED, mainTitle='Top Rated', pageFormat='top'))
	dir.Append(Function(DirectoryItem(MovieSort, L('Most Viewed')), url=XH_MOSTVIEWED, mainTitle='Most Viewed', pageFormat='top'))
	dir.Append(Function(InputDirectoryItem(Search, L('Search'), L('Search'), thumb=R(ICON)), url=XH_SEARCH, mainTitle='Search', pageFormat='search'))
	dir.Append(PrefsItem(title="Preferences", thumb=R(ICON_PREFS)))
	return dir

def ChannelsMenu(sender):
	dir = MediaContainer(title2 = sender.itemTitle)
	pageContent = HTML.ElementFromURL(XH_CHANNELS, cacheTime=CACHE_1WEEK)
	for channelItem in pageContent.xpath('//table[@id="channels"]/tr/td/a'):
		channelItemTitle = channelItem.xpath('div[@style="font-size:18px; font-weight:bold;"]')[0].text.strip()
		channelItemTitle = re.sub(r'[,0-9()]','', channelItemTitle).strip()
		channelItemUrl = channelItem.get('href')
		channelItemThumb = channelItem.xpath('div[@align="center"]/img')[0].get('src')
		dir.Append(Function(DirectoryItem(MovieSort, L(channelItemTitle), thumb=Function(channelThumb, url=channelItemThumb)), url=channelItemUrl, mainTitle=channelItemTitle, pageFormat='channel'))
	return dir

def MovieSort(sender,url,page=1,mainTitle='',searchQuery='',pageFormat='',sortBy='',timeFrame=''):
	if pageFormat == 'top':
		dir = MediaContainer(title2 = mainTitle)
		dir.Append(Function(DirectoryItem(MovieList, L('7 Days')), url=url, mainTitle='Weekly '+mainTitle, pageFormat=pageFormat, timeFrame='weekly'))
		dir.Append(Function(DirectoryItem(MovieList, L('30 Days')), url=url, mainTitle='Monthly '+mainTitle, pageFormat=pageFormat, timeFrame='monthly'))
		dir.Append(Function(DirectoryItem(MovieList, L('All Time')), url=url, mainTitle='All Time '+mainTitle, pageFormat=pageFormat, timeFrame='alltime'))
	elif pageFormat == 'channel':
		dir = MediaContainer(title2 = 'Channel: '+mainTitle+' | Sort by:')
		dir.Append(Function(DirectoryItem(MovieList, L('Date Added')), url=url, mainTitle='Channel: '+mainTitle, pageFormat=pageFormat, sortBy='new'))
		dir.Append(Function(DirectoryItem(MovieList, L('View Count')), url=url, mainTitle='Channel: '+mainTitle, pageFormat=pageFormat, sortBy='views'))
		dir.Append(Function(DirectoryItem(MovieList, L('Rating')), url=url, mainTitle='Channel: '+mainTitle, pageFormat=pageFormat, sortBy='rating'))
	elif pageFormat == 'search':
		searchQueryCapitalized = searchQuery.replace('+',' ').capitalize()
		dir = MediaContainer(title2 = 'Search: '+searchQueryCapitalized+' | Sort by:')
		dir.Append(Function(DirectoryItem(MovieList, L('Relevance')), url=url, mainTitle=mainTitle, searchQuery=searchQuery, pageFormat=pageFormat, sortBy=''))
		dir.Append(Function(DirectoryItem(MovieList, L('Date Added')), url=url, mainTitle=mainTitle, searchQuery=searchQuery, pageFormat=pageFormat, sortBy='da'))
		dir.Append(Function(DirectoryItem(MovieList, L('View Count')), url=url, mainTitle=mainTitle, searchQuery=searchQuery, pageFormat=pageFormat, sortBy='vc'))
		dir.Append(Function(DirectoryItem(MovieList, L('Rating')), url=url, mainTitle=mainTitle, searchQuery=searchQuery, pageFormat=pageFormat, sortBy='rt'))
	return dir

def MovieList(sender,url,page=1,mainTitle='',searchQuery='',pageFormat='normal',sortBy='',timeFrame=''):
	pageFormatOne = ['top','latest']
	pageFormatTwo = ['channel','search']
	if pageFormat == 'top':
		dir = MediaContainer(title2 = mainTitle)
		pageContent = HTML.ElementFromURL(url % timeFrame)
		initialXpath = '//tr[@bgcolor="#F2F2F2" or @bgcolor="#F8F8F8"]'
	elif pageFormat == 'latest':
		dir = MediaContainer(title2 = mainTitle)
		pageContent = HTML.ElementFromURL(url)
		initialXpath = '//tr[@bgcolor="#F2F2F2" or @bgcolor="#F8F8F8"]'
	elif pageFormat == 'channel':
		dir = MediaContainer(title2 = mainTitle+' | Page: '+str(page), replaceParent=(page>1))
		channel = url.replace('/channels/','')
		channel = channel.replace(sortBy+'-','')
		channel = channel.replace('-'+str(page),'')
		channel = channel.replace('.html','')
		pageContent = HTML.ElementFromURL(XH_CHANNEL % (sortBy,channel,page))
		initialXpath = '//td[contains(@id,"t_")]'
	elif pageFormat == 'search':
		searchQueryCapitalized = searchQuery.replace('+',' ').capitalize()
		dir = MediaContainer(title2 = mainTitle+': '+searchQueryCapitalized+' | Page: '+str(page), replaceParent=(page>1))
		pageContent = HTML.ElementFromURL(XH_SEARCH % (searchQuery,page,Prefs['filterContent'].lower()))
		initialXpath = '//td[contains(@id,"t_")]'
	#Get prevPagination
	if page > 1:
		pageM = page-1
		dir.Append(Function(DirectoryItem(MovieList, L('+++Previous Page ('+str(pageM)+')+++')), url=url, page=pageM, mainTitle=mainTitle, searchQuery=searchQuery, pageFormat=pageFormat, sortBy=sortBy))
	for videoItem in pageContent.xpath(initialXpath):
		if pageFormat in pageFormatOne:
			videoItemTitle = videoItem.xpath('td/div[@class="moduleFeaturedTitle"]/a')[0].text.strip()
			videoItemLink  = XH_BASE + videoItem.xpath('td/div[@class="moduleFeaturedTitle"]/a')[0].get('href')
			videoItemThumb = videoItem.xpath('td/a/img')[0].get('src').replace('_','_b_')
			duration = videoItem.xpath('td/div[@class="moduleFeaturedDetails"]/p')[1].text.replace('Runtime: ','')
			duration = duration.replace('s','')
			duration = duration.replace('m',':')
			duration = duration.replace('h',':')
			videoItemDuration = GetDurationFromString(duration)
			videoItemViews = videoItem.xpath('td/div[@class="moduleFeaturedDetails"]/p')[2].text.replace('Views: ','')
			videoItemRating = (len(videoItem.xpath('td/div[@class="moduleFeaturedDetails"]/p/img[contains(@src,"/star.gif")]'))+(float(len(videoItem.xpath('td/div[@class="moduleFeaturedDetails"]/p/img[contains(@src,"/starhalf.gif")]')))/2))*2
			videoItemSummary = 'Duration: ' + duration
			videoItemSummary += '\r\nViews: ' + videoItemViews
			videoItemSummary += '\r\nRating: ' + str(videoItemRating)
		elif pageFormat in pageFormatTwo:
			videoItemTitle = videoItem.xpath('a/img')[0].get('alt').strip()
			videoItemLink  = XH_BASE + videoItem.xpath('a')[0].get('href')
			videoItemThumb = videoItem.xpath('a/img')[0].get('src').replace('_','_b_')
			duration = videoItem.xpath('div[@class="moduleFeaturedDetails"]')[0].text.replace('Runtime: ','')
			duration = duration.replace('s','')
			duration = duration.replace('m',':')
			duration = duration.replace('h',':')
			videoItemDuration = GetDurationFromString(duration)
			videoItemRating = (len(videoItem.xpath('img[contains(@src,"/star.gif")]'))+(float(len(videoItem.xpath('img[contains(@src,"/starhalf.gif")]')))/2))*2
			videoItemSummary = 'Duration: ' + duration
			videoItemSummary += '\r\nRating: ' + str(videoItemRating)
#		Log('videoItemTitle: '+videoItemTitle+' | videoItemLink: '+videoItemLink+' | videoItemThumb: '+videoItemThumb+' | videoItemSummary: '+videoItemSummary)
		dir.Append(Function(VideoItem(PlayVideo, title=videoItemTitle, summary=videoItemSummary, duration=videoItemDuration, rating=videoItemRating, thumb=Function(Thumb, url=videoItemThumb)), url=videoItemLink))
	#Get nextPagination
	pageP = page+1
	if len(pageContent.xpath('//span[@class="navNext"]/a')) > 0:
		dir.Append(Function(DirectoryItem(MovieList, L('+++Next Page ('+str(pageP)+')+++')), url=url, page=pageP, mainTitle=mainTitle, searchQuery=searchQuery, pageFormat=pageFormat, sortBy=sortBy))
	return dir

def Search(sender,url,mainTitle='',pageFormat='',query=''):
	dir = MediaContainer(noCache=True)
	searchQueryCorrect = query.replace(' ','+')
	dir = MovieSort(sender=None, url=url, mainTitle=mainTitle, pageFormat=pageFormat, searchQuery=searchQueryCorrect)
	return dir


####################################################################################################

def PlayVideo(sender, url):
	content = HTTP.Request(url).content
	vidurl = re.compile("'file': '(.+?)',").findall(content, re.DOTALL)
	if len(vidurl) > 0:
		gotovidurl = XH_PLAYER+vidurl[0]
		return Redirect(gotovidurl)
	else:
		return None
