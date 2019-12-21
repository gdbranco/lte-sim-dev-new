from pprint import pprint
import re
import json
import gzip
import pandas as pd
import numpy as np
class LTEParser:
    _mapa = {
        "B": "#Bearer",
        "T": "TimeStamp",
        "TX": "Transmission",
        "RX": "Receiver",
        "D": "Delay",
        "ID": "#Packet",
        "DST": "Destiny",
        "SRC": "Source",
        "SIZE": "Size"
    }
    def parse(self, inFile, flowDuration = 100):
        #VIDEO
        videoAverages = []
        videoFairness = []
        videoDelay = []
        videoJitter = []
        videoPLR = []
        #VOICE
        voiceAverages = []
        voiceFairness = []
        voiceDelay = []
        voiceJitter = []
        voicePLR = []
        #WEB
        WebAverages = []
        WebFairness = []
        WebDelay = []
        WebJitter = []
        WebPLR = []
        #CBR
        CBRAverages = []
        CBRFairness = []
        CBRDelay = []
        CBRJitter = []
        CBRPLR = []
        #GERAL
        packetLoss = []
        for sfile in inFile:
            content = ""
            print("Opening file: " + sfile)
            with gzip.open(sfile, 'rb') as file:
                content = file.read()
                content = content.decode('utf-8')
            print("\tParsing ...", end="")
            txContent, rxContent = self._parse(content)
            info = self.getFairnessIndex(rxContent, flowDuration)
            packetLossInfo = self.getPacketLossRatio(txContent, rxContent)
            delayInfo = self.getDelayJitter(rxContent)
            #VIDEO
            videoAverages.append(info['VIDEO']['Average'])
            videoFairness.append(info['VIDEO']['FairnessIndex'])
            videoDelay.append(delayInfo['VIDEO']['Average'])
            videoJitter.append(delayInfo['VIDEO']['StD'])
            videoPLR.append(packetLossInfo[1]['VIDEO'])
            #VOICE
            voiceAverages.append(info['VOIP']['Average'])
            voiceFairness.append(info['VOIP']['FairnessIndex'])
            voiceDelay.append(delayInfo['VOIP']['Average'])
            voiceJitter.append(delayInfo['VOIP']['StD'])
            voicePLR.append(packetLossInfo[1]['VOIP'])
            #WEBBUF
            WebAverages.append(info['WEB']['Average'])
            WebFairness.append(info['WEB']['FairnessIndex'])
            WebDelay.append(delayInfo['WEB']['Average'])
            WebJitter.append(delayInfo['WEB']['StD'])
            WebPLR.append(packetLossInfo[1]['WEB'])
            #CBRBUF
            CBRAverages.append(info['CBR']['Average'])
            CBRFairness.append(info['CBR']['FairnessIndex'])
            CBRDelay.append(delayInfo['CBR']['Average'])
            CBRJitter.append(delayInfo['CBR']['StD'])
            CBRPLR.append(packetLossInfo[1]['CBR'])
            #GERAL
            packetLoss.append(packetLossInfo[0])
        return [#VIDEO
                (sum(videoAverages)/len(videoAverages)),
                (sum(videoFairness)/len(videoFairness)),
                (sum(videoDelay)/len(videoDelay)),
                (sum(videoJitter)/len(videoJitter)),
                (sum(videoPLR)/len(videoPLR)),
                #VOICE
                (sum(voiceAverages)/len(voiceAverages)),
                (sum(voiceFairness)/len(voiceFairness)),
                (sum(voiceDelay)/len(voiceDelay)),
                (sum(voiceJitter)/len(voiceJitter)),
                (sum(voicePLR)/len(voicePLR)),
                #WEB
                (sum(WebAverages)/len(WebAverages)),
                (sum(WebFairness)/len(WebFairness)),
                (sum(WebDelay)/len(WebDelay)),
                (sum(WebJitter)/len(WebJitter)),
                (sum(WebPLR)/len(WebPLR)),
                #CBR
                (sum(CBRAverages)/len(CBRAverages)),
                (sum(CBRFairness)/len(CBRFairness)),
                (sum(CBRDelay)/len(CBRDelay)),
                (sum(CBRJitter)/len(CBRJitter)),
                (sum(CBRPLR)/len(CBRPLR)),
                #GERAL
                packetLoss]

    def _parse(self, content):
        txContent = self.parseTX(content)
        rxContent = self.parseRX(content)
        print("Done")
        return txContent, rxContent
    
    def parseTX(self, content):
        matches = re.findall(r"(^TX.+)", content, re.MULTILINE)
        if(matches == []):
            raise Exception("No matches in content for TX")
        dictPacketType = {"CBR": [], "VOIP": [], "VIDEO": [], "INF_BUF": [], "WEB": []}
        keys = dictPacketType.keys()
        for match in matches:
            values = match.split(' ')
            if values[1] in keys:
                tamanho = len(values)
                dic = {}
                for i in range(2, tamanho if tamanho%2==0 else tamanho-1, 2):
                    dic[LTEParser._mapa[values[i]]] = values[i+1]
                dic = dict(sorted(dic.items(), key=lambda x: x[0]))
                dictPacketType[values[1]].append(dic)
        return json.loads(json.dumps(dictPacketType))
        
    def parseRX(self, content):
        matches = re.findall(r"(^RX.+)", content, re.MULTILINE)
        if(matches == []):
            raise Exception("No matches in content for RX")
        dictPacketType = {"CBR": [], "VOIP": [], "VIDEO": [], "INF_BUF": [], "WEB": []}
        keys = dictPacketType.keys()
        for match in matches:
            values = match.split(' ')
            if values[1] in keys:
                tamanho = len(values)
                dic = {}
                for i in range(2, tamanho if tamanho%2==0 else tamanho-1, 2):
                    dic[LTEParser._mapa[values[i]]] = values[i+1]
                dic = dict(sorted(dic.items(), key=lambda x: x[0]))
                dictPacketType[values[1]].append(dic)
        return json.loads(json.dumps(dictPacketType))
    
    def getPacketLossRatio(self, txContent, rxContent):
        dictPacketType = {"CBR": [], "VOIP": [], "VIDEO": [], "INF_BUF": [], "WEB": []}
        tx_pkts = 0
        rx_pkts = 0
        for key in txContent:
            keytx = len(txContent[key])
            tx_pkts += keytx
            keyrx = len(rxContent[key])
            rx_pkts += keyrx
            keyPLR = ((keytx - keyrx) / (keytx if keytx != 0 else 1)) * 100
            dictPacketType[key] = keyPLR
        plr = ((tx_pkts - rx_pkts) / tx_pkts) * 100
        return plr, dictPacketType
    
    def getDelayJitter(self, rxContent):
        delayPerApp = {}
        for app in rxContent:
            delayPerApp[app] = {"Sum": 0, "Average": 0, "StD": 0}
            delayPerApp[app]["Sum"] = sum(float(item["Delay"]) for item in rxContent[app])
            tamanho = len(rxContent[app])
            delayPerApp[app]["Average"] = (delayPerApp[app]["Sum"]/tamanho) if tamanho != 0 else 0
            delayPerApp[app]["StD"] = (sum((float(item["Delay"]) - delayPerApp[app]["Average"])**2 for item in rxContent[app])/ (tamanho - 1)) if tamanho-1 != 0 else 0
        return delayPerApp
    
    def getGoodput(self, rxContent, flowDuration):
        gputPerApp = {}
        for app in rxContent:
            gputPerApp[app] = {"Sum": 0, "Average": 0}
            gputPerApp[app]["Sum"] = sum(float(item["Size"])*8 for item in rxContent[app])
            gputPerApp[app]["Average"] = (gputPerApp[app]["Sum"])/flowDuration
        return gputPerApp
    
    def getThroughput(self, rxContent, flowDuration):
        tputPerApp = {}
        for app in rxContent:
            tputPerApp[app] = {"Sum": 0, "Average": 0}
            tputPerApp[app]["Sum"] = sum((float(item["Size"]) + 5)*8 for item in rxContent[app])
            tputPerApp[app]["Average"] = (tputPerApp[app]["Sum"])/flowDuration
        return tputPerApp
    
    def getSpectralEff():
        pass
    
    def getFairnessIndex(self, rxContent, flowDuration):
        fairnessPerApp = {}
        for app in rxContent:
            fairnessPerApp[app] = {"Sum": 0, "Average": 0, "SumSquared": 0, "SquaredSum": 0, "FairnessIndex": 0}
            if(len(rxContent[app]) > 0):
                fairnessPerApp[app]["Sum"] = sum(float(item["Size"])*8 for item in rxContent[app])
                fairnessPerApp[app]["Average"] = (fairnessPerApp[app]["Sum"])/flowDuration
                fairnessPerApp[app]["SumSquared"] = sum(pow(float(item["Size"])*8,2) for item in rxContent[app])
                fairnessPerApp[app]["SquaredSum"] = pow(fairnessPerApp[app]["Sum"], 2)
                division = (len(rxContent[app]) * fairnessPerApp[app]["SumSquared"])
                fairnessPerApp[app]["FairnessIndex"] = fairnessPerApp[app]["SquaredSum"] / division if division > 0 else 1
        return fairnessPerApp


    def getFiles(self, base, graphicsbase, scheds, users, until):
        files = {}
        ext = ".gz"
        for sched in range(1,scheds):
            files[sched] = {}
            for ue in range(10, users, 10):
                files[sched][ue] = []
                for count in range(1,until):
                    file = "SCHED_" + str(sched) + "_UE_" + str(ue) + "_" + str(count)
                    filename = base + file + ext
                    files[sched][ue].append(filename)
        return files

class Graphics:
    def __init__(self, graphicsbase, metrics):
        self.graphicsbase = graphicsbase
        self.metrics = metrics

    def gputFile(self, kind, pfEnabled, newEnabled):
        MEGAWEB = {1: [], 2: [], 3: [], 4: [], 5: [], 6: [], 7: [], 8: []}
        dfGPUTWEB = None
        for sched in self.metrics[kind]["GPUTS"]:
            MEGAWEB[sched] = np.true_divide(self.metrics[kind]["GPUTS"][sched], 1e+6)
        if(pfEnabled and newEnabled):
                dfGPUTWEB = pd.DataFrame({'PF': MEGAWEB[1],
                        'FLS': MEGAWEB[4], 'EXPR': MEGAWEB[5], 'LOGR': MEGAWEB[6],
                        'EXPFLS': MEGAWEB[7], 'LOGFLS': MEGAWEB[8]},
                        index=[10,20,30,40,50])
        elif(pfEnabled):
            dfGPUTWEB = pd.DataFrame({'PF': MEGAWEB[1],
                        'FLS': MEGAWEB[4], 'EXPR': MEGAWEB[5], 'LOGR': MEGAWEB[6]},
                        index=[10,20,30,40,50])
        elif(newEnabled):
            dfGPUTWEB = pd.DataFrame({
                        'FLS': MEGAWEB[4], 'EXPR': MEGAWEB[5], 'LOGR': MEGAWEB[6],
                        'EXPFLS': MEGAWEB[7], 'LOGFLS': MEGAWEB[8]},
                        index=[10,20,30,40,50])
        else:
            dfGPUTWEB = pd.DataFrame({'FLS': MEGAWEB[4], 'EXPR': MEGAWEB[5], 'LOGR': MEGAWEB[6]},
                        index=[10,20,30,40,50])
        plot = dfGPUTWEB.plot(rot=0, marker='o')
        plot.set(xlabel="Usuários", ylabel="Vazão (MB/s)")
        plot.legend(loc='best', bbox_to_anchor=(1.0, 0.5))
        fig = plot.get_figure()
        fig.savefig(self.graphicsbase + "GPUT" + kind + "_PF-"+ str(pfEnabled) + "_new-" + str(newEnabled) + ".pdf", bbox_inches='tight')

    def delayFile(self, kind, pfEnabled, newEnabled):
        self.makeGraph(kind, "DELAY", "Latência (s)", pfEnabled, newEnabled)

    def jitterFile(self, kind, pfEnabled, newEnabled):
        self.makeGraph(kind, "JITTER", "Variância latência (s)", pfEnabled, newEnabled)

    def fairnessFile(self, kind, pfEnabled, newEnabled):
        self.makeGraph(kind, "FAIR", "Índice de justiça", pfEnabled, newEnabled)

    def plrFile(self, kind, pfEnabled, newEnabled):
        self.makeGraph(kind, "PLR", "Perda de pacotes (%)", pfEnabled, newEnabled)

    def makeGraph(self, kind, metric,yLabel, pfEnabled, newEnabled):
        df = None
        if(pfEnabled and newEnabled):
            df = pd.DataFrame({'PF': self.metrics[kind][metric][1],
                            'FLS': self.metrics[kind][metric][4], 'EXPR': self.metrics[kind][metric][5], 'LOGR': self.metrics[kind][metric][6],
                            'EXPFLS': self.metrics[kind][metric][7], 'LOGFLS': self.metrics[kind][metric][8]},
                            index=[10,20,30,40,50])
        elif(pfEnabled):
                df = pd.DataFrame({'PF': self.metrics[kind][metric][1],
                            'FLS': self.metrics[kind][metric][4], 'EXPR': self.metrics[kind][metric][5], 'LOGR': self.metrics[kind][metric][6]},
                            index=[10,20,30,40,50])
        elif(newEnabled):
            df = pd.DataFrame({'FLS': self.metrics[kind][metric][4],
                            'EXPR': self.metrics[kind][metric][5], 'LOGR': self.metrics[kind][metric][6],
                            'EXPFLS': self.metrics[kind][metric][7], 'LOGFLS': self.metrics[kind][metric][8]},
                            index=[10,20,30,40,50])
        else:
            df = pd.DataFrame({'FLS': self.metrics[kind][metric][4],
                                        'EXPR': self.metrics[kind][metric][5], 'LOGR': self.metrics[kind][metric][6]},
                            index=[10,20,30,40,50])
        plot = df.plot.bar(rot=0)
        plot.set(xlabel="Usuários", ylabel=yLabel)
        plot.legend(loc='best', bbox_to_anchor=(1.0, 0.5))
        fig = plot.get_figure()
        fig.savefig(self.graphicsbase + metric + kind + "_PF-"+ str(pfEnabled) + "_new-" + str(newEnabled) + ".pdf", bbox_inches='tight')