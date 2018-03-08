# -*- coding:utf-8 -*-
#=====================================
# 通过分析所有代码，找出没有用到的图片
# 没有用的图片资源主要有如下3种情况:
# (1)png => code
# (2)png => csd,   csd   => code
# (3)
#	 1. png => plist, plist => code
#    2. png => plist, plist => ExportJson, ExportJson => code
# (4)
#    1. png => fnt, fnt => code
#    2. png => fnt, fnt=>csd, csd => code
#=====================================

import os
import shutil

global g_cnt
g_cnt = 0
def getCnt():
	global g_cnt
	g_cnt = g_cnt + 1
	return g_cnt

#===================================
# @brief 读取所有图片到列表里面
#===================================
def readPicNameList(picPath):
	picNameList = []
	for prePath, folderList, fileNameList in os.walk(picPath):
		for fileName in fileNameList:
			suffixName = fileName[-3:]
			if "png" == suffixName or "jpg" == suffixName:
				picNameList.append([fileName, prePath])
	return picNameList
	# print("read PicNameList ok")

#===============================================
# @brief 读取文件目录下某个后缀的数据到列表里面
#===============================================
def readFileDataToList(filePath, suffixName):
	n = len(suffixName)
	saveToList = []
	for prePath, folderList, fileNameList in os.walk(filePath):
		for fileName in fileNameList:
			# fielSuffixName = fileName[-3:]
			fielSuffixName = fileName[-n:]
			if suffixName == fielSuffixName:
				f = open(prePath+"/"+fileName, "rb")
				data = f.read()
				# saveToList.append([data, fileName, prePath+"/"+fileName])
				saveToList.append([data, fileName, prePath])
				f.close()
	return saveToList


#===================================
# @brief 在数据列表里面检查
#===================================
def checkInDataList(keyword, dataList, show):#, n):
	# 各种情况如下:
	# csd:   <FileData Type="Normal" Path="Res/abc.png" />
	# code:  ["abc"] = "abc.png",
	#        cc.Sprite:create("res/abc/abc.png")
	# plist: <key>abc.png</key>
	#
	# 规律如下：
	# (1)" (2)' (3)/ (4)>
	for index in range(0, len(dataList)):
		fileInfo = dataList[index]
		findIndex = fileInfo[0].find(keyword)
		if -1 != findIndex:
			preCh = fileInfo[0][findIndex-1]
			if '"'==preCh or "'"==preCh or "/"==preCh or ">"==preCh:
				return index
	return -1

#==========================
# @brief 处理没有用的文件
#==========================
def handleNotFoundFile(filePathList):
	for fileInfo in filePathList:
		fileName = fileInfo[0]
		filePath = fileInfo[1]
		if not os.path.exists("needdelete/"+filePath):
			os.makedirs("needdelete/"+filePath)
		shutil.copyfile(filePath+"/"+fileName, "needdelete/"+filePath+"/"+fileName)


#==========================
# @brief 在代码里面处理
#==========================
def handleInCode(picIndex, picNameList, codeDataList):
	picName = picNameList[picIndex][0]
	index = checkInDataList(picName, codeDataList, False)
	return -1!=index

#==========================
# @brief 在csd里面处理
#==========================
def handleInCsd(picIndex, picNameList, csdDataList,codeDataList):
	picName = picNameList[picIndex][0]
	#pic => csd
	csdIndex = checkInDataList(picName, csdDataList, False)
	if -1 != csdIndex:
		fileName = csdDataList[csdIndex][1]
		# csd => code
		codeIndex = checkInDataList(fileName[:-1]+"b", codeDataList, False)
		if -1 == codeIndex:
			print(getCnt(), picName, fileName, "pic=>csd")
			handleNotFoundFile([
				(picName, picNameList[picIndex][1]),
				(fileName, csdDataList[csdIndex][2])])
			return True
	return False

#==========================
# @brief 在plist里面处理
#==========================
def handleInPlist(picIndex, picNameList, plistDataList, exportJsonDataList, codeDataList):
	picName = picNameList[picIndex][0]
	#pic => plist
	plistIndex = checkInDataList(picName, plistDataList, False)
	if -1 != plistIndex:
		plistFileName = plistDataList[plistIndex][1]
		codeIndex = checkInDataList(plistFileName, codeDataList, False)
		# plist => code
		if -1 != codeIndex:
			#代码里面找到plist
			return True
		else:
			exportJsonIndex = checkInDataList(plistFileName, exportJsonDataList, False)
			# plist = > exportJston
			if -1 != exportJsonIndex:
				exportJsonFileName = exportJsonDataList[exportJsonIndex][1]
				codeIndex = checkInDataList(exportJsonFileName, codeDataList, False)
				# exportJston => code
				if -1 == codeIndex:
					print(getCnt(), picName, plistFileName, exportJsonFileName, "pic=>plist=>json")
					handleNotFoundFile([
						(picName, picNameList[picIndex][1]),
						(plistFileName, plistDataList[plistIndex][2]),
						(exportJsonFileName, exportJsonDataList[exportJsonIndex][2])])
					return True
	return False

#==========================
# @brief 在fnt里面处理
#==========================
def handleInFnt(picIndex, picNameList, fntDataList, csdDataList, codeDataList):
	picName = picNameList[picIndex][0]
	#pic => fnt
	fntIndex = checkInDataList(picName, fntDataList, False)
	if -1 != fntIndex:
		# fnt => code
		fntName = fntDataList[fntIndex][1]
		codeIndex = checkInDataList(fntName, codeDataList, False)
		if -1 != codeIndex:
			return True
		else:
			#fnt => csd
			csdIndex = checkInDataList(fntName, csdDataList, False)
			if -1 != csdIndex:
				csdFileName = csdDataList[csdIndex][1]
				# csd => code
				codeIndex = checkInDataList(csdFileName[:-1]+"b", codeDataList, False)
				if -1 == codeIndex:
					print(getCnt(), picName, csdFileName, "pic=>fnt=>csd")
					handleNotFoundFile([
						(picName, picNameList[picIndex][1]),
						(csdFileName, csdDataList[csdIndex][2])])
					return True
	return False


#===============================================================
# @brief 查找没用的图片
# @params picPath  要查找的图片路径
#         codePath 要查找的代码路径
#         csdPath  要查找的csd路径(只有csd才能用来查询,csb不行)
#         plist    要查找的plist路径
#         fntPath  要查找的fnt路径
#===============================================================
def findNotUsePic(picPath, codePath, csdPath, plistPath, fntPath):
	picNameList   = readPicNameList(picPath)

	codeDataList  	   = readFileDataToList(codePath, "lua")
	csdDataList   	   = readFileDataToList(csdPath,  "csd")
	plistDataList 	   = readFileDataToList(plistPath,"plist")
	fntDataList   	   = readFileDataToList(fntPath,  "fnt")
	exportJsonDataList = readFileDataToList(fntPath,  "ExportJson")

	for picIndex in range(0, len(picNameList)):
		# code
		if handleInCode(picIndex, picNameList, codeDataList):
			pass
		# csd
		elif handleInCsd(picIndex, picNameList, csdDataList, codeDataList):
			pass
		# plist, exportJson
		elif handleInPlist(picIndex, picNameList, plistDataList, exportJsonDataList, codeDataList):
			pass
		# fnt
		elif handleInFnt(picIndex, picNameList, fntDataList, csdDataList, codeDataList):
			pass


if "__main__" == __name__:
	findNotUsePic("./src", "./src", "./ccs_pro", "./src", "./src")
	print("ok")
