/* -*- Mode:C++; c-file-style:"gnu"; indent-tabs-mode:nil; -*- */
/*
 * Copyright (c) 2010,2011,2012,2013 TELEMATICS LAB, Politecnico di Bari
 *
 * This file is part of LTE-Sim
 *
 * LTE-Sim is free software; you can redistribute it and/or modify
 * it under the terms of the GNU General Public License version 3 as
 * published by the Free Software Foundation;
 *
 * LTE-Sim is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU General Public License for more details.
 *
 * You should have received a copy of the GNU General Public License
 * along with LTE-Sim; if not, see <http://www.gnu.org/licenses/>.
 *
 * Author: Giuseppe Piro <g.piro@poliba.it>
 */

#include "../channel/LteChannel.h"
#include "../phy/enb-lte-phy.h"
#include "../phy/ue-lte-phy.h"
#include "../core/spectrum/bandwidth-manager.h"
#include "../networkTopology/Cell.h"
#include "../protocolStack/packet/packet-burst.h"
#include "../protocolStack/packet/Packet.h"
#include "../core/eventScheduler/simulator.h"
#include "../flows/application/WEB.h"
#include "../flows/application/VoIP.h"
#include "../flows/application/CBR.h"
#include "../flows/application/TraceBased.h"
#include "../device/IPClassifier/ClassifierParameters.h"
#include "../flows/QoS/QoSParameters.h"
#include "../flows/QoS/QoSForEXP.h"
#include "../flows/QoS/QoSForFLS.h"
#include "../flows/QoS/QoSForM_LWDF.h"
#include "../componentManagers/FrameManager.h"
#include "../utility/seed.h"
#include "../utility/RandomVariable.h"
#include "../channel/propagation-model/macrocell-urban-area-channel-realization.h"
#include "../phy/wideband-cqi-eesm-error-model.h"
#include "../phy/simple-error-model.h"
#include "../load-parameters.h"
#include <iostream>
#include <vector>
#include <queue>
#include <fstream>
#include <cstdlib>
#include <cstring>
#include <ctime>
#include <cmath>

std::vector<int> chunks(int num, std::vector<double> p)
{
	std::vector<int> a;
	int left = num;
	for (int i = 0; i < p.size(); i++)
	{
		double avg = num * p[i];
		a.push_back((int)(avg));
		left -= (int)(avg);
	}
	while (left)
	{
		a[left] += 1;
		left--;
	}
	return a;
}

string selectTraceFile(string video_trace, int videoBitRate){
	string retorno;
	switch (videoBitRate)
	{
		case 128:
			retorno = path + "src/flows/application/Trace/" + video_trace + "128k.dat";
			std::cout << "		selected video @ 128k" << std::endl;
			break;
		case 242:
			retorno = path + "src/flows/application/Trace/" + video_trace + "242k.dat";
			std::cout << "		selected video @ 242k" << std::endl;
			break;
		case 440:
			retorno = path + "src/flows/application/Trace/" + video_trace + "440k.dat";
			std::cout << "		selected video @ 440k" << std::endl;
			break;
		default:
			retorno = path + "src/flows/application/Trace/" + video_trace + "128k.dat";
			std::cout << "		selected video @ 128k as default" << std::endl;
			break;
	}
	return retorno;
}

ENodeB::DLSchedulerType selectScheduler(int sched_type)
{
	switch (sched_type)
	{
	case 1:
		std::cout << "Scheduler PF " << std::endl;
		return ENodeB::DLScheduler_TYPE_PROPORTIONAL_FAIR;
	case 2:
		std::cout << "Scheduler MLWDF " << std::endl;
		return ENodeB::DLScheduler_TYPE_MLWDF;
	case 3:
		std::cout << "Scheduler EXP " << std::endl;
		return ENodeB::DLScheduler_TYPE_EXP;
	case 4:
		std::cout << "Scheduler FLS " << std::endl;
		return ENodeB::DLScheduler_TYPE_FLS;
	case 5:
		std::cout << "Scheduler EXP_RULE " << std::endl;
		return ENodeB::DLScheduler_EXP_RULE;
	case 6:
		std::cout << "Scheduler LOG RULE " << std::endl;
		return ENodeB::DLScheduler_LOG_RULE;
	case 7:
		std::cout << "Scheduler FLS_EXP " << std::endl;
		return ENodeB::DLScheduler_FLSEXP;
	default:
		return ENodeB::DLScheduler_TYPE_PROPORTIONAL_FAIR;
	}
}

QoSParameters *selectQosParameters(ENodeB::DLSchedulerType downlink_scheduler_type, double maxDelay)
{
	QoSParameters *qos;
	switch (downlink_scheduler_type)
	{
	case ENodeB::DLScheduler_TYPE_FLS:
	case ENodeB::DLScheduler_FLSEXP:
		qos = new QoSForFLS();
		if (maxDelay == 0.1)
		{
			std::cout << "Target Delay = 0.1 s, M = 9" << std::endl;
			((QoSForFLS *)qos)->SetNbOfCoefficients(9);
		}
		else if (maxDelay == 0.08)
		{
			std::cout << "Target Delay = 0.08 s, M = 7" << std::endl;
			((QoSForFLS *)qos)->SetNbOfCoefficients(7);
		}
		else if (maxDelay == 0.06)
		{
			std::cout << "Target Delay = 0.06 s, M = 5" << std::endl;
			((QoSForFLS *)qos)->SetNbOfCoefficients(5);
		}
		else if (maxDelay == 0.04)
		{
			std::cout << "Target Delay = 0.04 s, M = 3" << std::endl;
			((QoSForFLS *)qos)->SetNbOfCoefficients(3);
		}
		else
		{
			std::cout << "ERROR: target delay is not available" << std::endl;
		}
		break;
	case ENodeB::DLScheduler_TYPE_MAXIMUM_THROUGHPUT:
		qos = new QoSForM_LWDF();
		break;
	case ENodeB::DLScheduler_TYPE_EXP:
		qos = new QoSForEXP();
		break;
	default:
		qos = new QoSParameters();
		break;
	}
	qos->SetMaxDelay(maxDelay);
	return qos;
}

static void SingleCellWithoutInterference(double radius,
										  int nbUE,
										  double pVoIP, double pVideo, double pWEB, double pCBR,
										  int sched_type,
										  int speed,
										  double maxDelay, int videoBitRate)
{
	if ((pVoIP + pVideo + pWEB + pCBR) * 100 != 100)
	{
		std::cout << "Percentages of flows must sum 1";
		return;
	}
	else if (nbUE % 10 != 0)
	{
		std::cout << "Number os users must be a multiple of 10";
		return;
	}
	std::vector<double> p = {pVoIP, pVideo, pWEB, pCBR};
	std::vector<int> a = chunks(nbUE, p);
	// define simulation times
	double duration = 100;
	double flow_duration = 100;

	double bandwidth = 1.4;

	// CREATE COMPONENT MANAGER
	Simulator *simulator = Simulator::Init();
	FrameManager *frameManager = FrameManager::Init();
	NetworkManager *networkManager = NetworkManager::Init();

	// CONFIGURE SEED
	int seed = -1;
	if (seed >= 0)
	{
		int commonSeed = GetCommonSeed(seed);
		srand(commonSeed);
	}
	else
	{
		srand(time(NULL));
	}
	std::cout << "Simulation with SEED = " << seed << std::endl;

	// SET SCHEDULING ALLOCATION SCHEME
	ENodeB::DLSchedulerType downlink_scheduler_type = selectScheduler(sched_type);

	// SET FRAME STRUCTURE
	frameManager->SetFrameStructure(FrameManager::FRAME_STRUCTURE_FDD);

	// CREATE CELL
	CartesianCoordinates center = GetCartesianCoordinatesForCell(0, radius * 1000.);
	Cell *cell = new Cell(0, radius, 0.035, center.GetCoordinateX(), center.GetCoordinateY());
	networkManager->GetCellContainer()->push_back(cell);
	std::cout << "Created Cell, id " << cell->GetIdCell()
			  << ", position: " << cell->GetCellCenterPosition()->GetCoordinateX()
			  << " " << cell->GetCellCenterPosition()->GetCoordinateY() << std::endl;

	// CREATE SPECTRUM
	BandwidthManager *spectrum = new BandwidthManager(bandwidth, bandwidth, 0, 0);

	// CREATE CHANNELS and propagation loss model
	LteChannel *dlCh = new LteChannel();
	LteChannel *ulCh = new LteChannel();
	dlCh->SetChannelId(0);
	ulCh->SetChannelId(0);

	//Create ENodeB
	ENodeB *enb = new ENodeB(1, cell);
	enb->GetPhy()->SetDlChannel(dlCh);
	enb->GetPhy()->SetUlChannel(ulCh);
	enb->SetDLScheduler(downlink_scheduler_type);
	enb->GetPhy()->SetBandwidthManager(spectrum);
	std::cout << "Created enb, id " << enb->GetIDNetworkNode()
			  << ", cell id " << enb->GetCell()->GetIdCell()
			  << ", position: " << enb->GetMobilityModel()->GetAbsolutePosition()->GetCoordinateX()
			  << " " << enb->GetMobilityModel()->GetAbsolutePosition()->GetCoordinateY()
			  << ", channels id " << enb->GetPhy()->GetDlChannel()->GetChannelId()
			  << enb->GetPhy()->GetUlChannel()->GetChannelId() << std::endl;
	spectrum->Print();
	ulCh->AddDevice((NetworkNode *)enb);
	networkManager->GetENodeBContainer()->push_back(enb);

	//Define Application Container
	int nbCell = 1;
	int nbVoipUE = a[0];
	int nbVideoUE = a[1];
	int nbWebUE = a[2];
	int nbCbrUE = a[3];
	VoIP VoIPApplication[nbCell * nbVoipUE];
	TraceBased VideoApplication[nbCell * nbVideoUE];
	WEB WEBApplication[nbCell * nbWebUE];
	CBR CBRApplication[nbCell * nbCbrUE];
	int voipApplication = 0;
	int videoApplication = 0;
	int cbrApplication = 0;
	int WebApplication = 0;
	int destinationPort = 101;
	int applicationID = 0;

	//Create GW
	Gateway *gw = new Gateway();
	networkManager->GetGatewayContainer()->push_back(gw);

	//Create UEs
	int idUE = 1;
	for (int i = 0; i < nbUE; i++)
	{
		//ue's random position
		double posX = (double)rand() / RAND_MAX;
		posX = 0.95 *
			   (((2 * radius * 1000) * posX) - (radius * 1000));
		double posY = (double)rand() / RAND_MAX;
		posY = 0.95 *
			   (((2 * radius * 1000) * posY) - (radius * 1000));
		double speedDirection = GetRandomVariable(360.) * ((2 * 3.14) / 360);

		UserEquipment *ue = new UserEquipment(idUE,
											  posX, posY, speed, speedDirection,
											  cell,
											  enb,
											  0, //handover false!
											  Mobility::CONSTANT_POSITION);

		std::cout << "Created UE - id " << idUE << " position " << posX << " " << posY << std::endl;

		ue->GetMobilityModel()->GetAbsolutePosition()->Print();
		ue->GetPhy()->SetDlChannel(enb->GetPhy()->GetDlChannel());
		ue->GetPhy()->SetUlChannel(enb->GetPhy()->GetUlChannel());

		FullbandCqiManager *cqiManager = new FullbandCqiManager();
		cqiManager->SetCqiReportingMode(CqiManager::PERIODIC);
		cqiManager->SetReportingInterval(1);
		cqiManager->SetDevice(ue);
		ue->SetCqiManager(cqiManager);

		WidebandCqiEesmErrorModel *errorModel = new WidebandCqiEesmErrorModel();
		ue->GetPhy()->SetErrorModel(errorModel);

		networkManager->GetUserEquipmentContainer()->push_back(ue);

		// register ue to the enb
		enb->RegisterUserEquipment(ue);
		// define the channel realization
		MacroCellUrbanAreaChannelRealization *c_dl = new MacroCellUrbanAreaChannelRealization(enb, ue);
		enb->GetPhy()->GetDlChannel()->GetPropagationLossModel()->AddChannelRealization(c_dl);
		MacroCellUrbanAreaChannelRealization *c_ul = new MacroCellUrbanAreaChannelRealization(ue, enb);
		enb->GetPhy()->GetUlChannel()->GetPropagationLossModel()->AddChannelRealization(c_ul);

		// CREATE DOWNLINK APPLICATION FOR THIS UE
		double start_time = 0.5 + GetRandomVariable(5.);
		double duration_time = start_time + flow_duration;

		// *** voip application
		if (i < nbVoipUE)
		{
			// create application
			VoIPApplication[voipApplication].SetSource(gw);
			VoIPApplication[voipApplication].SetDestination(ue);
			VoIPApplication[voipApplication].SetApplicationID(applicationID);
			VoIPApplication[voipApplication].SetStartTime(start_time);
			VoIPApplication[voipApplication].SetStopTime(duration_time);

			// create qos parameters
			QoSParameters *qos = selectQosParameters(downlink_scheduler_type, maxDelay);
			VoIPApplication[voipApplication].SetQoSParameters(qos);
			//create classifier parameters
			ClassifierParameters *cp = new ClassifierParameters(gw->GetIDNetworkNode(),
																ue->GetIDNetworkNode(),
																0,
																destinationPort,
																TransportProtocol::TRANSPORT_PROTOCOL_TYPE_UDP);
			VoIPApplication[voipApplication].SetClassifierParameters(cp);

			std::cout << "CREATED VOIP APPLICATION, ID " << applicationID << std::endl;

			//update counter
			destinationPort++;
			applicationID++;
			voipApplication++;
		}

		// *** video application
		if (i < (nbVoipUE + nbVideoUE) && i >= nbVoipUE)
		{
			// create application
			VideoApplication[videoApplication].SetSource(gw);
			VideoApplication[videoApplication].SetDestination(ue);
			VideoApplication[videoApplication].SetApplicationID(applicationID);
			VideoApplication[videoApplication].SetStartTime(start_time);
			VideoApplication[videoApplication].SetStopTime(duration_time);

			string video_trace("foreman_H264_");
			//string video_trace ("highway_H264_");
			//string video_trace ("mobile_H264_");
			string _file(selectTraceFile(video_trace, videoBitRate));
			VideoApplication[videoApplication].SetTraceFile(_file);
			// create qos parameters
			QoSParameters* qos = selectQosParameters(downlink_scheduler_type, maxDelay);
			VideoApplication[videoApplication].SetQoSParameters(qos);
			//create classifier parameters
			ClassifierParameters *cp = new ClassifierParameters(gw->GetIDNetworkNode(),
																ue->GetIDNetworkNode(),
																0,
																destinationPort,
																TransportProtocol::TRANSPORT_PROTOCOL_TYPE_UDP);
			VideoApplication[videoApplication].SetClassifierParameters(cp);

			std::cout << "CREATED VIDEO APPLICATION, ID " << applicationID << std::endl;

			//update counter
			destinationPort++;
			applicationID++;
			videoApplication++;
		}

		// *** web application
		if (i < (nbVoipUE + nbVideoUE + nbWebUE) && i >= (nbVoipUE + nbVideoUE))
		{
			// create application
			WEBApplication[WebApplication].SetSource(gw);
			WEBApplication[WebApplication].SetDestination(ue);
			WEBApplication[WebApplication].SetApplicationID(applicationID);
			WEBApplication[WebApplication].SetStartTime(start_time);
			WEBApplication[WebApplication].SetStopTime(duration_time);

			// create qos parameters
			QoSParameters *qosParameters = selectQosParameters(downlink_scheduler_type, maxDelay);
			WEBApplication[WebApplication].SetQoSParameters(qosParameters);

			//create classifier parameters
			ClassifierParameters *cp = new ClassifierParameters(gw->GetIDNetworkNode(),
																ue->GetIDNetworkNode(),
																0,
																destinationPort,
																TransportProtocol::TRANSPORT_PROTOCOL_TYPE_UDP);
			WEBApplication[WebApplication].SetClassifierParameters(cp);

			std::cout << "CREATED WEB APPLICATION, ID " << applicationID << std::endl;

			//update counter
			destinationPort++;
			applicationID++;
			WebApplication++;
		}

		// *** cbr application
		if (i < (nbVoipUE + nbVideoUE + nbWebUE + nbCbrUE) && i >= (nbVoipUE + nbVideoUE + nbWebUE))
		{
			// create application
			CBRApplication[cbrApplication].SetSource(gw);
			CBRApplication[cbrApplication].SetDestination(ue);
			CBRApplication[cbrApplication].SetApplicationID(applicationID);
			CBRApplication[cbrApplication].SetStartTime(start_time);
			CBRApplication[cbrApplication].SetStopTime(duration_time);
			CBRApplication[cbrApplication].SetInterval(0.04);
			CBRApplication[cbrApplication].SetSize(5);

			// create qos parameters
			QoSParameters *qosParameters = selectQosParameters(downlink_scheduler_type, maxDelay);
			CBRApplication[cbrApplication].SetQoSParameters(qosParameters);

			//create classifier parameters
			ClassifierParameters *cp = new ClassifierParameters(gw->GetIDNetworkNode(),
																ue->GetIDNetworkNode(),
																0,
																destinationPort,
																TransportProtocol::TRANSPORT_PROTOCOL_TYPE_UDP);
			CBRApplication[cbrApplication].SetClassifierParameters(cp);

			std::cout << "CREATED CBR APPLICATION, ID " << applicationID << std::endl;

			//update counter
			destinationPort++;
			applicationID++;
			cbrApplication++;
		}
		idUE++;
	}

	simulator->SetStop(duration);
	simulator->Run();
	delete simulator;
}
