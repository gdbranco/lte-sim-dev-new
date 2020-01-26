from pprint import pprint
import re
import json
import gzip
import pandas as pd
import numpy as np
import scipy.stats
import matplotlib.pyplot as plt
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
                "PLR": {1: [], 2: [], 3: [], 4: [], 5: [], 6: [], 7:[], 8: []},
                "qtdUsuarios": {1: [], 2: [], 3: [], 4: [], 5: [], 6: [], 7:[], 8: []},
                "qtdUsuariosAtendidos": {1: [], 2: [], 3: [], 4: [], 5: [], 6: [], 7:[], 8: []},
                "qtdReq": {1: [], 2: [], 3: [], 4: [], 5: [], 6: [], 7:[], 8: []},
                "qtdReqAtendidas": {1: [], 2: [], 3: [], 4: [], 5: [], 6: [], 7:[], 8: []}
            },
            "VOIP":{
                "GPUT": {1: [], 2: [], 3: [], 4: [], 5: [], 6: [], 7:[], 8: []},
                "FAIR": {1: [], 2: [], 3: [], 4: [], 5: [], 6: [], 7:[], 8: []},
                "DELAY": {1: [], 2: [], 3: [], 4: [], 5: [], 6: [], 7:[], 8: []},
                "JITTER": {1: [], 2: [], 3: [], 4: [], 5: [], 6: [], 7:[], 8: []},
                "PLR": {1: [], 2: [], 3: [], 4: [], 5: [], 6: [], 7:[], 8: []},
                "qtdUsuarios": {1: [], 2: [], 3: [], 4: [], 5: [], 6: [], 7:[], 8: []},
                "qtdUsuariosAtendidos": {1: [], 2: [], 3: [], 4: [], 5: [], 6: [], 7:[], 8: []},
                "qtdReq": {1: [], 2: [], 3: [], 4: [], 5: [], 6: [], 7:[], 8: []},
                "qtdReqAtendidas": {1: [], 2: [], 3: [], 4: [], 5: [], 6: [], 7:[], 8: []}
            },
            "WEB":{
                "GPUT": {1: [], 2: [], 3: [], 4: [], 5: [], 6: [], 7:[], 8: []},
                "FAIR": {1: [], 2: [], 3: [], 4: [], 5: [], 6: [], 7:[], 8: []},
                "DELAY": {1: [], 2: [], 3: [], 4: [], 5: [], 6: [], 7:[], 8: []},
                "JITTER": {1: [], 2: [], 3: [], 4: [], 5: [], 6: [], 7:[], 8: []},
                "PLR": {1: [], 2: [], 3: [], 4: [], 5: [], 6: [], 7:[], 8: []},
                "qtdUsuarios": {1: [], 2: [], 3: [], 4: [], 5: [], 6: [], 7:[], 8: []},
                "qtdUsuariosAtendidos": {1: [], 2: [], 3: [], 4: [], 5: [], 6: [], 7:[], 8: []},
                "qtdReq": {1: [], 2: [], 3: [], 4: [], 5: [], 6: [], 7:[], 8: []},
                "qtdReqAtendidas": {1: [], 2: [], 3: [], 4: [], 5: [], 6: [], 7:[], 8: []}
            },
            "CBR":{
                "GPUT": {1: [], 2: [], 3: [], 4: [], 5: [], 6: [], 7:[], 8: []},
                "FAIR": {1: [], 2: [], 3: [], 4: [], 5: [], 6: [], 7:[], 8: []},
                "DELAY": {1: [], 2: [], 3: [], 4: [], 5: [], 6: [], 7:[], 8: []},
                "JITTER": {1: [], 2: [], 3: [], 4: [], 5: [], 6: [], 7:[], 8: []},
                "PLR": {1: [], 2: [], 3: [], 4: [], 5: [], 6: [], 7:[], 8: []},
                "qtdUsuarios": {1: [], 2: [], 3: [], 4: [], 5: [], 6: [], 7:[], 8: []},
                "qtdUsuariosAtendidos": {1: [], 2: [], 3: [], 4: [], 5: [], 6: [], 7:[], 8: []},
                "qtdReq": {1: [], 2: [], 3: [], 4: [], 5: [], 6: [], 7:[], 8: []},
                "qtdReqAtendidas": {1: [], 2: [], 3: [], 4: [], 5: [], 6: [], 7:[], 8: []}
            },
            "GERAL": {
                "PLR": {1: [], 2: [], 3: [], 4: [], 5: [], 6: [], 7:[], 8: []}
            }
        }

        for sched in range(1, scheds):
            for ue in range(10, users, 10):
                info = self._schedParse(files[sched][ue], 100)
                for app in metrics:
                    for metric in metrics[app]:
                        metrics[app][metric][sched].append(info[app][metric])
        return metrics
        
    def _schedParse(self, inFiles, flowDuration):
        #VIDEO
        infoList = {
            "VIDEO": {
                "CI": [],
                "AVERAGES": [],
                "FAIRNESS": [],
                "qtdUsuarios": [],
                "qtdUsuariosAtendidos": [],
                "qtdReq": [],
                "qtdReqAtendidas": [],
                "DELAYS": [],
                "JITTERS": [],
                "PLRS": []
            },
            "VOIP": {
                "CI": [],
                "AVERAGES": [],
                "FAIRNESS": [],
                "qtdUsuarios": [],
                "qtdUsuariosAtendidos": [],
                "qtdReq": [],
                "qtdReqAtendidas": [],
                "DELAYS": [],
                "JITTERS": [],
                "PLRS": []
            },
            "WEB": {
                "CI": [],
                "AVERAGES": [],
                "FAIRNESS": [],
                "qtdUsuarios": [],
                "qtdUsuariosAtendidos": [],
                "qtdReq": [],
                "qtdReqAtendidas": [],
                "DELAYS": [],
                "JITTERS": [],
                "PLRS": []
            },
            "CBR": {
                "CI": [],
                "AVERAGES": [],
                "FAIRNESS": [],
                "qtdUsuarios": [],
                "qtdUsuariosAtendidos": [],
                "qtdReq": [],
                "qtdReqAtendidas": [],
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
            info = self.getFairnessIndex(rxContent, txContent, flowDuration)
            packetLossInfo = self.getPacketLossRatio(txContent, rxContent)
            delayInfo = self.getDelayJitter(rxContent)
            #VIDEO
            infoList['VIDEO']['AVERAGES'].append(info['VIDEO']['Average'])
            infoList['VIDEO']['FAIRNESS'].append(info['VIDEO']['FairnessIndex'])
            infoList['VIDEO']['qtdUsuarios'].append(info['VIDEO']['qtdUsuarios'])
            infoList['VIDEO']['qtdUsuariosAtendidos'].append(info['VIDEO']['qtdUsuariosAtendidos'])
            infoList['VIDEO']['qtdReq'].append(info['VIDEO']['qtdReq'])
            infoList['VIDEO']['qtdReqAtendidas'].append(info['VIDEO']['qtdReqAtendidas'])
            infoList['VIDEO']['DELAYS'].append(delayInfo['VIDEO']['Average'])
            infoList['VIDEO']['JITTERS'].append(delayInfo['VIDEO']['StD'])
            infoList['VIDEO']['PLRS'].append(packetLossInfo[1]['VIDEO'])
            #VOIP
            infoList['VOIP']['AVERAGES'].append(info['VOIP']['Average'])
            infoList['VOIP']['FAIRNESS'].append(info['VOIP']['FairnessIndex'])
            infoList['VOIP']['qtdUsuarios'].append(info['VOIP']['qtdUsuarios'])
            infoList['VOIP']['qtdUsuariosAtendidos'].append(info['VOIP']['qtdUsuariosAtendidos'])
            infoList['VOIP']['qtdReq'].append(info['VOIP']['qtdReq'])
            infoList['VOIP']['qtdReqAtendidas'].append(info['VOIP']['qtdReqAtendidas'])
            infoList['VOIP']['DELAYS'].append(delayInfo['VOIP']['Average'])
            infoList['VOIP']['JITTERS'].append(delayInfo['VOIP']['StD'])
            infoList['VOIP']['PLRS'].append(packetLossInfo[1]['VOIP'])
            #WEB
            infoList['WEB']['AVERAGES'].append(info['WEB']['Average'])
            infoList['WEB']['FAIRNESS'].append(info['WEB']['FairnessIndex'])
            infoList['WEB']['qtdUsuarios'].append(info['WEB']['qtdUsuarios'])
            infoList['WEB']['qtdUsuariosAtendidos'].append(info['WEB']['qtdUsuariosAtendidos'])
            infoList['WEB']['qtdReq'].append(info['WEB']['qtdReq'])
            infoList['WEB']['qtdReqAtendidas'].append(info['WEB']['qtdReqAtendidas'])
            infoList['WEB']['DELAYS'].append(delayInfo['WEB']['Average'])
            infoList['WEB']['JITTERS'].append(delayInfo['WEB']['StD'])
            infoList['WEB']['PLRS'].append(packetLossInfo[1]['WEB'])
            #CBRBUF
            infoList['CBR']['AVERAGES'].append(info['CBR']['Average'])
            infoList['CBR']['FAIRNESS'].append(info['CBR']['FairnessIndex'])
            infoList['CBR']['qtdUsuarios'].append(info['CBR']['qtdUsuarios'])
            infoList['CBR']['qtdUsuariosAtendidos'].append(info['CBR']['qtdUsuariosAtendidos'])
            infoList['CBR']['qtdReq'].append(info['CBR']['qtdReq'])
            infoList['CBR']['qtdReqAtendidas'].append(info['CBR']['qtdReqAtendidas'])
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
                    "CI": self._mean_confidence_interval(infoList['VIDEO']['FAIRNESS']),
                },
                "DELAY": {
                    "MEAN": np.mean(infoList['VIDEO']['DELAYS']),
                    "CI": self._mean_confidence_interval(infoList['VIDEO']['DELAYS'])
                },
                "qtdUsuarios": np.mean(infoList["VIDEO"]["qtdUsuarios"]),
                "qtdUsuariosAtendidos": np.mean(infoList["VIDEO"]["qtdUsuariosAtendidos"]),
                "qtdReq": np.mean(infoList['VIDEO']['qtdReq']),
                "qtdReqAtendidas": np.mean(infoList['VIDEO']['qtdReqAtendidas']),
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
                "qtdUsuarios": np.mean(infoList["VOIP"]["qtdUsuarios"]),
                "qtdUsuariosAtendidos": np.mean(infoList["VOIP"]["qtdUsuariosAtendidos"]),
                "qtdReq": np.mean(infoList['VOIP']['qtdReq']),
                "qtdReqAtendidas": np.mean(infoList['VOIP']['qtdReqAtendidas']),
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
                "qtdUsuarios": np.mean(infoList["WEB"]["qtdUsuarios"]),
                "qtdUsuariosAtendidos": np.mean(infoList["WEB"]["qtdUsuariosAtendidos"]),
                "qtdReq": np.mean(infoList['WEB']['qtdReq']),
                "qtdReqAtendidas": np.mean(infoList['WEB']['qtdReqAtendidas']),
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
                "qtdUsuarios": np.mean(infoList["CBR"]["qtdUsuarios"]),
                "qtdUsuariosAtendidos": np.mean(infoList["CBR"]["qtdUsuariosAtendidos"]),
                "qtdReq": np.mean(infoList['CBR']['qtdReq']),
                "qtdReqAtendidas": np.mean(infoList['CBR']['qtdReqAtendidas']),
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
        dictPacketType = {"CBR": [], "VOIP": [], "VIDEO": [], "WEB": []}
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
        dictPacketType = {"CBR": [], "VOIP": [], "VIDEO": [], "WEB": []}
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
        dictPacketType = {"CBR": [], "VOIP": [], "VIDEO": [], "WEB": []}
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
            tputPerApp[app]["Sum"] = sum(((float(item["Size"]))*8 + 5) for item in rxContent[app])
            tputPerApp[app]["Average"] = (tputPerApp[app]["Sum"])/flowDuration
        return tputPerApp
    
    def getSpectralEff():
        pass
    
    def getTotalUsersTXApp(self, txContent):
        txAppUser = {}
        for app in txContent:
            txAppUser[app] = txAppUser.get(app, {})
            for tx in txContent[app]:
                bearer = tx["#Bearer"]
                txAppUser[app][bearer] = txAppUser[app].get(bearer, [])
        return txAppUser
                

    def getFairnessIndex(self, rxContent, txContent, flowDuration):
        rxAppUser = {}
        fairness = {}
        txAppUser = self.getTotalUsersTXApp(txContent)
        for app in rxContent:
            rxAppUser[app] = rxAppUser.get(app, {})
            for rx in rxContent[app]:
                bearer = rx["#Bearer"]
                rxAppUser[app][bearer] = rxAppUser[app].get(bearer, [])
                rxAppUser[app][bearer].append(float(rx["Size"])*8)
        
        for app in rxAppUser:
            localUserGput = []
            for user in rxAppUser[app]:
                localUserGput.append(sum(rxAppUser[app][user])/flowDuration)

            averageAppGput = sum(localUserGput)
            sumSquared = sum([pow(item,2) for item in localUserGput])
            squaredSum = pow(sum(localUserGput),2)

            fairness[app] = fairness.get(app, {})
            usuariosApp = len(txAppUser[app])
            reqsApp = len(txContent[app])
            division = (usuariosApp * sumSquared)
            fairness[app]["FairnessIndex"] = (squaredSum/division) if division > 0 else 0
            fairness[app]["Average"] = averageAppGput
            fairness[app]["qtdUsuarios"] = usuariosApp
            fairness[app]["qtdUsuariosAtendidos"] = len(rxAppUser[app])
            fairness[app]['qtdReq'] = reqsApp
            fairness[app]['qtdReqAtendidas'] = len(rxContent[app])
        return fairness

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
        
    def plrGeralFile(self):
        averagePacketLoss = {}
        for key in self.metrics["GERAL"]["PLR"]:
            averagePacketLoss[key] = []
            for i in range(0, 5):
                average = np.mean(self.metrics["GERAL"]["PLR"][key][i])
                averagePacketLoss[key].append(average)
        dfLossRatio = pd.DataFrame({'PF': averagePacketLoss[1],
                            'FLS': averagePacketLoss[4], 'EXPR': averagePacketLoss[5], 'LOGR': averagePacketLoss[6],
                           'EXPFLS': averagePacketLoss[7], 'LOGFLS': averagePacketLoss[8]},
                           index=[10,20,30,40,50])
        plot = dfLossRatio.plot.bar(rot=0)
        
        # Shrink current axis's height by 10% on the bottom
        box = plot.get_position()
        plot.set_position([box.x0, box.y0 + box.height * 0.1,
                        box.width, box.height * 0.9])

        # Put a legend below current axis
        plot.legend(loc='upper center', bbox_to_anchor=(0.5, -0.15),
          fancybox=True, shadow=True, ncol=5)
        plot.set(xlabel="Usuários", ylabel="Perda de pacotes (%)")
        fig = plot.get_figure()
        fig.savefig(self.graphicsbase + "PacketLossRatio.pdf", bbox_inches='tight')

    def makeGraph(self, kind, metric,yLabel, pfEnabled, newEnabled):
        df = None
        _metric = {1: [], 2: [], 3: [], 4: [], 5: [], 6: [], 7: [], 8: []}
        _error = {1: [], 2: [], 3: [], 4: [], 5: [], 6: [], 7: [], 8: []}
        __xticks = {}
        __xticksAtendidos = {}
        _xticks = []
        for sched in self.metrics[kind][metric]:
            _metric[sched] = [tipo["MEAN"] for tipo in self.metrics[kind][metric][sched]]
            _error[sched] = [tipo["CI"] for tipo in self.metrics[kind][metric][sched]]

            for i in [10,20,30,40,50]:
                __xticks[i] = __xticks.get(i, [])
                __xticksAtendidos[i] = __xticksAtendidos.get(i, [])
                __xticks[i].append(self.metrics[kind]["qtdUsuarios"][sched][(i//10)-1])
                __xticksAtendidos[i].append(self.metrics[kind]["qtdUsuariosAtendidos"][sched][(i//10)-1])

        for i in [10,20,30,40,50]:
            mediaTotal = np.mean(__xticks[i])
            mediaAtendido = np.mean(__xticksAtendidos[i])
            if(metric == "FAIR"):
                _xticks.append(str(int(100*(mediaAtendido/mediaTotal))) + "%(" + str(int(mediaTotal))+")")
            else:
                _xticks.append(str(int(mediaTotal)))


        fig, ax = plt.subplots()
        ind = np.arange(5)                # the x locations for the groups
        width = 0.1                    # the width of the bars
        _error_kw = dict(elinewidth=2,ecolor='dimgray')
        ax.set_xlim(-width*3,len(ind)-width)
        ax.set_xticks(ind+width)

        # Plot errors on top
        if(pfEnabled and newEnabled):
            for index,i in enumerate([1,4,5,6,7,8]):
                ax.bar(ind+width*index, _metric[i], width, yerr=_error[i], error_kw=_error_kw)
                legenda = ('PF','FLS','EXPR','LOGR','EXPFLS','LOGFLS')
        elif(pfEnabled):
            for index,i in enumerate([1,4,5,6]):
                ax.bar(ind+width*index, _metric[i], width, yerr=_error[i], error_kw=_error_kw)
                legenda = ('PF','FLS','EXPR','LOGR')
        elif(newEnabled):
            for index,i in enumerate([4,5,6,7,8]):
                ax.bar(ind+width*index, _metric[i], width, yerr=_error[i], error_kw=_error_kw)
                legenda = ('FLS','EXPR','LOGR','EXPFLS','LOGFLS')
        else:
            for index,i in enumerate([4,5,6]):
                ax.bar(ind+width*index, _metric[i], width, yerr=_error[i], error_kw=_error_kw)
                legenda = ('FLS','EXPR','LOGR')

        # Shrink current axis's height by 10% on the bottom
        box = ax.get_position()
        ax.set_position([box.x0, box.y0 + box.height * 0.1,
                        box.width, box.height * 0.9])

        # Put a legend below current axis
        ax.legend(legenda,loc='upper center', bbox_to_anchor=(0.5, -0.15),
          fancybox=True, shadow=True, ncol=5)
        ax.set(xlabel="Usuários", ylabel=yLabel)
        ax.set_xticklabels(_xticks)
        fig = ax.get_figure()
        fig.savefig(self.graphicsbase + metric + kind + "_PF-"+ str(pfEnabled) + "_new-" + str(newEnabled) + ".pdf", bbox_inches='tight')