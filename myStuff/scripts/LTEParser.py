from pprint import pprint
import re
import json
import gzip
import pandas as pd
import numpy as np
import scipy.stats
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
    def parse(self, base, graphicsbase, scheds, users, until, flowDuration = 100):
        files = self.getFiles(base, graphicsbase, scheds, users, until)
        metrics = {
            "VIDEO":{
                "GPUT": {1: [], 2: [], 3: [], 4: [], 5: [], 6: [], 7:[], 8: []},
                "FAIR": {1: [], 2: [], 3: [], 4: [], 5: [], 6: [], 7:[], 8: []},
                "DELAY": {1: [], 2: [], 3: [], 4: [], 5: [], 6: [], 7:[], 8: []},
                "JITTER": {1: [], 2: [], 3: [], 4: [], 5: [], 6: [], 7:[], 8: []},
                "PLR": {1: [], 2: [], 3: [], 4: [], 5: [], 6: [], 7:[], 8: []}
            },
            "VOICE":{
                "GPUT": {1: [], 2: [], 3: [], 4: [], 5: [], 6: [], 7:[], 8: []},
                "FAIR": {1: [], 2: [], 3: [], 4: [], 5: [], 6: [], 7:[], 8: []},
                "DELAY": {1: [], 2: [], 3: [], 4: [], 5: [], 6: [], 7:[], 8: []},
                "JITTER": {1: [], 2: [], 3: [], 4: [], 5: [], 6: [], 7:[], 8: []},
                "PLR": {1: [], 2: [], 3: [], 4: [], 5: [], 6: [], 7:[], 8: []}
            },
            "WEB":{
                "GPUT": {1: [], 2: [], 3: [], 4: [], 5: [], 6: [], 7:[], 8: []},
                "FAIR": {1: [], 2: [], 3: [], 4: [], 5: [], 6: [], 7:[], 8: []},
                "DELAY": {1: [], 2: [], 3: [], 4: [], 5: [], 6: [], 7:[], 8: []},
                "JITTER": {1: [], 2: [], 3: [], 4: [], 5: [], 6: [], 7:[], 8: []},
                "PLR": {1: [], 2: [], 3: [], 4: [], 5: [], 6: [], 7:[], 8: []}
            },
            "CBR":{
                "GPUT": {1: [], 2: [], 3: [], 4: [], 5: [], 6: [], 7:[], 8: []},
                "FAIR": {1: [], 2: [], 3: [], 4: [], 5: [], 6: [], 7:[], 8: []},
                "DELAY": {1: [], 2: [], 3: [], 4: [], 5: [], 6: [], 7:[], 8: []},
                "JITTER": {1: [], 2: [], 3: [], 4: [], 5: [], 6: [], 7:[], 8: []},
                "PLR": {1: [], 2: [], 3: [], 4: [], 5: [], 6: [], 7:[], 8: []}
            },
            "GERAL": {
            "PLR": {1: [], 2: [], 3: [], 4: [], 5: [], 6: [], 7:[], 8: []}
            }
        }

        for sched in range(1, scheds):
            for ue in range(10, users, 10):
                info = self._schedParse(files[sched][ue], 100)
                #VIDEO
                metrics["VIDEO"]["GPUT"][sched].append(info["VIDEO"]["GPUT"])
                metrics["VIDEO"]["FAIR"][sched].append(info["VIDEO"]["FAIR"])
                metrics["VIDEO"]["DELAY"][sched].append(info["VIDEO"]["DELAY"])
                metrics["VIDEO"]["JITTER"][sched].append(info["VIDEO"]["JITTER"])
                metrics["VIDEO"]["PLR"][sched].append(info["VIDEO"]["PLR"])
                #VOICE
                metrics["VOICE"]["GPUT"][sched].append(info["VOIP"]["GPUT"])
                metrics["VOICE"]["FAIR"][sched].append(info["VOIP"]["FAIR"])
                metrics["VOICE"]["DELAY"][sched].append(info["VOIP"]["DELAY"])
                metrics["VOICE"]["JITTER"][sched].append(info["VOIP"]["JITTER"])
                metrics["VOICE"]["PLR"][sched].append(info["VOIP"]["PLR"])
                #WEB
                metrics["WEB"]["GPUT"][sched].append(info["WEB"]["GPUT"])
                metrics["WEB"]["FAIR"][sched].append(info["WEB"]["FAIR"])
                metrics["WEB"]["DELAY"][sched].append(info["WEB"]["DELAY"])
                metrics["WEB"]["JITTER"][sched].append(info["WEB"]["JITTER"])
                metrics["WEB"]["PLR"][sched].append(info["WEB"]["PLR"])
                #CBR
                metrics["CBR"]["GPUT"][sched].append(info["CBR"]["GPUT"])
                metrics["CBR"]["FAIR"][sched].append(info["CBR"]["FAIR"])
                metrics["CBR"]["DELAY"][sched].append(info["CBR"]["DELAY"])
                metrics["CBR"]["JITTER"][sched].append(info["CBR"]["JITTER"])
                metrics["CBR"]["PLR"][sched].append(info["CBR"]["PLR"])
                #GERAL
                metrics["GERAL"]["PLR"][sched].append(info["GERAL"]["PLR"])
                
        return metrics
        
    def _schedParse(self, inFiles, flowDuration):
        #VIDEO
        infoList = {
            "VIDEO": {
                "CI": [],
                "AVERAGES": [],
                "FAIRNESS": [],
                "DELAYS": [],
                "JITTERS": [],
                "PLRS": []
            },
            "VOIP": {
                "CI": [],
                "AVERAGES": [],
                "FAIRNESS": [],
                "DELAYS": [],
                "JITTERS": [],
                "PLRS": []
            },
            "WEB": {
                "CI": [],
                "AVERAGES": [],
                "FAIRNESS": [],
                "DELAYS": [],
                "JITTERS": [],
                "PLRS": []
            },
            "CBR": {
                "CI": [],
                "AVERAGES": [],
                "FAIRNESS": [],
                "DELAYS": [],
                "JITTERS": [],
                "PLRS": []
            },
            "GERAL": {
                "PLRS": []
            }
        }
        for sfile in inFiles:
            content = ""
            print("Opening file: " + sfile)
            with gzip.open(sfile, 'rb') as file:
                content = file.read()
                content = content.decode('utf-8')
            print("\tParsing ...", end="")
            txContent, rxContent = self._singleParse(content)
            info = self.getFairnessIndex(rxContent, flowDuration)
            packetLossInfo = self.getPacketLossRatio(txContent, rxContent)
            delayInfo = self.getDelayJitter(rxContent)
            #VIDEO
            infoList['VIDEO']['AVERAGES'].append(info['VIDEO']['Average'])
            infoList['VIDEO']['FAIRNESS'].append(info['VIDEO']['FairnessIndex'])
            infoList['VIDEO']['DELAYS'].append(delayInfo['VIDEO']['Average'])
            infoList['VIDEO']['JITTERS'].append(delayInfo['VIDEO']['StD'])
            infoList['VIDEO']['PLRS'].append(packetLossInfo[1]['VIDEO'])
            #VOICE
            infoList['VOIP']['AVERAGES'].append(info['VOIP']['Average'])
            infoList['VOIP']['FAIRNESS'].append(info['VOIP']['FairnessIndex'])
            infoList['VOIP']['DELAYS'].append(delayInfo['VOIP']['Average'])
            infoList['VOIP']['JITTERS'].append(delayInfo['VOIP']['StD'])
            infoList['VOIP']['PLRS'].append(packetLossInfo[1]['VOIP'])
            #WEB
            infoList['WEB']['AVERAGES'].append(info['WEB']['Average'])
            infoList['WEB']['FAIRNESS'].append(info['WEB']['FairnessIndex'])
            infoList['WEB']['DELAYS'].append(delayInfo['WEB']['Average'])
            infoList['WEB']['JITTERS'].append(delayInfo['WEB']['StD'])
            infoList['WEB']['PLRS'].append(packetLossInfo[1]['WEB'])
            #CBRBUF
            infoList['CBR']['AVERAGES'].append(info['CBR']['Average'])
            infoList['CBR']['FAIRNESS'].append(info['CBR']['FairnessIndex'])
            infoList['CBR']['DELAYS'].append(delayInfo['CBR']['Average'])
            infoList['CBR']['JITTERS'].append(delayInfo['CBR']['StD'])
            infoList['CBR']['PLRS'].append(packetLossInfo[1]['CBR'])
            #GERAL
            infoList['GERAL']['PLRS'].append(packetLossInfo[0])
        
        info = {
            "VIDEO": {
                "GPUT": {
                    "MEAN": np.true_divide(np.mean(infoList['VIDEO']['AVERAGES']),1e+6),
                    "CI": np.true_divide(self._mean_confidence_interval(infoList['VIDEO']['AVERAGES']),1e+6)
                },
                "FAIR": {
                    "MEAN": np.mean(infoList['VIDEO']['FAIRNESS']),
                    "CI": self._mean_confidence_interval(infoList['VIDEO']['FAIRNESS'])
                },
                "DELAY": {
                    "MEAN": np.mean(infoList['VIDEO']['DELAYS']),
                    "CI": self._mean_confidence_interval(infoList['VIDEO']['DELAYS'])
                },
                "JITTER": {
                    "MEAN": np.mean(infoList['VIDEO']['JITTERS']),
                    "CI": self._mean_confidence_interval(infoList['VIDEO']['JITTERS'])
                },
                "PLR": {
                    "MEAN": np.mean(infoList['VIDEO']['PLRS']),
                    "CI": self._mean_confidence_interval(infoList['VIDEO']['PLRS'])
                }
            },
            "VOIP": {
                "GPUT": {
                    "MEAN": np.true_divide(np.mean(infoList['VOIP']['AVERAGES']),1e+6),
                    "CI": np.true_divide(self._mean_confidence_interval(infoList['VOIP']['AVERAGES']),1e+6)
                },
                "FAIR": {
                    "MEAN": np.mean(infoList['VOIP']['FAIRNESS']),
                    "CI": self._mean_confidence_interval(infoList['VOIP']['FAIRNESS'])
                },
                "DELAY": {
                    "MEAN": np.mean(infoList['VOIP']['DELAYS']),
                    "CI": self._mean_confidence_interval(infoList['VOIP']['DELAYS'])
                },
                "JITTER": {
                    "MEAN": np.mean(infoList['VOIP']['JITTERS']),
                    "CI": self._mean_confidence_interval(infoList['VOIP']['JITTERS'])
                },
                "PLR": {
                    "MEAN": np.mean(infoList['VOIP']['PLRS']),
                    "CI": self._mean_confidence_interval(infoList['VOIP']['PLRS'])
                }
            },
            "WEB": {
                "GPUT": {
                    "MEAN": np.true_divide(np.mean(infoList['WEB']['AVERAGES']),1e+6),
                    "CI": np.true_divide(self._mean_confidence_interval(infoList['WEB']['AVERAGES']),1e+6)
                },
                "FAIR": {
                    "MEAN": np.mean(infoList['WEB']['FAIRNESS']),
                    "CI": self._mean_confidence_interval(infoList['WEB']['FAIRNESS'])
                },
                "DELAY":{
                    "MEAN": np.mean(infoList['WEB']['DELAYS']),
                    "CI": self._mean_confidence_interval(infoList['WEB']['DELAYS'])
                },
                "JITTER": {
                    "MEAN": np.mean(infoList['WEB']['JITTERS']),
                    "CI": self._mean_confidence_interval(infoList['WEB']['JITTERS'])
                },
                "PLR": {
                    "MEAN": np.mean(infoList['WEB']['PLRS']),
                    "CI": self._mean_confidence_interval(infoList['WEB']['PLRS'])
                }
            },
            "CBR": {
                "GPUT": {
                    "MEAN": np.true_divide(np.mean(infoList['CBR']['AVERAGES']),1e+6),
                    "CI": np.true_divide(self._mean_confidence_interval(infoList['CBR']['AVERAGES']),1e+6)
                },
                "FAIR": {
                    "MEAN": np.mean(infoList['CBR']['FAIRNESS']),
                    "CI": self._mean_confidence_interval(infoList['CBR']['FAIRNESS'])
                },
                "DELAY": {
                    "MEAN": np.mean(infoList['CBR']['DELAYS']),
                    "CI": self._mean_confidence_interval(infoList['CBR']['DELAYS'])
                },
                "JITTER": {
                    "MEAN": np.mean(infoList['CBR']['JITTERS']),
                    "CI": self._mean_confidence_interval(infoList['CBR']['JITTERS'])
                },
                "PLR": {
                    "MEAN": np.mean(infoList['CBR']['PLRS']),
                    "CI": self._mean_confidence_interval(infoList['CBR']['PLRS'])
                }
            },
            "GERAL": {
                "PLR": infoList['GERAL']['PLRS']
            }
        }
        return info

    def _mean_confidence_interval(self, data, confidence=0.95):
        a = 1.0 * np.array(data)
        n = len(a)
        m, se = np.mean(a), scipy.stats.sem(a)
        h = se * scipy.stats.t.ppf((1 + confidence) / 2., n-1)
        return h

    def _singleParse(self, content):
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
        self.makeGraph(kind, "GPUT", "Vazão (MB/s)", pfEnabled, newEnabled)

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
        _metric = {1: [], 2: [], 3: [], 4: [], 5: [], 6: [], 7: [], 8: []}
        for sched in self.metrics[kind][metric]:
            _metric[sched] = [tipo["MEAN"] for tipo  in self.metrics[kind][metric][sched]]
        if(pfEnabled and newEnabled):
            df = pd.DataFrame({'PF': _metric[1],
                            'FLS': _metric[4], 'EXPR': _metric[5], 'LOGR': _metric[6],
                            'EXPFLS': _metric[7], 'LOGFLS': _metric[8]},
                            index=[10,20,30,40,50])
        elif(pfEnabled):
                df = pd.DataFrame({'PF': _metric[1],
                            'FLS': _metric[4], 'EXPR': _metric[5], 'LOGR': _metric[6]},
                            index=[10,20,30,40,50])
        elif(newEnabled):
            df = pd.DataFrame({'FLS': _metric[4],
                            'EXPR': _metric[5], 'LOGR': _metric[6],
                            'EXPFLS': _metric[7], 'LOGFLS': _metric[8]},
                            index=[10,20,30,40,50])
        else:
            df = pd.DataFrame({'FLS': _metric[4],
                                        'EXPR': _metric[5], 'LOGR': _metric[6]},
                            index=[10,20,30,40,50])
        plot = None
        if(metric == "GPUT"):
            plot = df.plot(rot=0, marker='o')
        else:
            plot = df.plot.bar(rot=0)
        plot.set(xlabel="Usuários", ylabel=yLabel)
        plot.legend(loc='lower right', bbox_to_anchor=(1.2, 0))
        fig = plot.get_figure()
        fig.savefig(self.graphicsbase + metric + kind + "_PF-"+ str(pfEnabled) + "_new-" + str(newEnabled) + ".pdf", bbox_inches='tight')