#include "dl-expfls-packet-scheduler.h"


DL_FLSEXP_PacketScheduler::DL_FLSEXP_PacketScheduler(ENodeB::DLSchedulerType scheduler)
{
	SetMacEntity(0);
	CreateFlowsToSchedule();
	m_runControlLaw = true;
	m_subFrameCounter = 0;
	internalMetric = scheduler;
}

DL_FLSEXP_PacketScheduler::~DL_FLSEXP_PacketScheduler()
{
	Destroy();
}

void DL_FLSEXP_PacketScheduler::DoSchedule()
{
#ifdef SCHEDULER_DEBUG
	std::cout << "Start DL packet (FLS) scheduler for node "
			  << GetMacEntity()->GetDevice()->GetIDNetworkNode() << std::endl;
#endif

	UpdateDataToTransmitAndAverageDataRate();
	CheckForDLDropPackets();

	m_subFrameCounter++;
	if (m_runControlLaw)
	{
		RunControlLaw();
	}
	if (m_subFrameCounter == 10)
	{
		m_runControlLaw = true;
		m_subFrameCounter = 0;
	}

	Select_FlowsToSchedule();
	m_avgHOLDelayes = ComputeAverageOfHOLDelays();

	if (GetFlowsToSchedule()->size() != 0)
	{
		RBsAllocation();
	}
	StopSchedule();
}

void DL_FLSEXP_PacketScheduler::DoStopSchedule(void)
{
#ifdef SCHEDULER_DEBUG
	std::cout << "\t Do Stop Schedule (FLS) Creating Packet Burst" << std::endl;
#endif

	PacketBurst *pb = new PacketBurst();

	//Create Packet Burst
	FlowsToSchedule *flowsToSchedule = GetFlowsToSchedule();

	for (FlowsToSchedule::iterator it = flowsToSchedule->begin(); it != flowsToSchedule->end(); it++)
	{
		FlowToSchedule *flow = (*it);

		int availableBytes = flow->GetAllocatedBits() / 8;

		if (availableBytes > 0)
		{
			flow->GetBearer()->UpdateTransmittedBytes(availableBytes);
#ifdef SCHEDULER_DEBUG
			std::cout << "\t  --> add packets for flow "
					  << flow->GetBearer()->GetApplication()->GetApplicationID() << std::endl;
#endif

			//flow->GetBearer ()->GetMacQueue ()->PrintQueueInfo ();
			RlcEntity *rlc = flow->GetBearer()->GetRlcEntity();
			PacketBurst *pb2 = rlc->TransmissionProcedure(availableBytes);

#ifdef SCHEDULER_DEBUG
			std::cout << "\t\t  nb of packets: " << pb2->GetNPackets() << std::endl;
#endif
			if (pb2->GetNPackets() > 0)
			{
				std::list<Packet *> packets = pb2->GetPackets();
				std::list<Packet *>::iterator it;
				for (it = packets.begin(); it != packets.end(); it++)
				{
#ifdef SCHEDULER_DEBUG
					std::cout << "\t\t  added packet of bytes " << (*it)->GetSize() << std::endl;
					//(*it)->Print ();
#endif

					Packet *p = (*it);
					pb->AddPacket(p->Copy());
				}
			}
			delete pb2;
		}
	}
	//SEND PACKET BURST
#ifdef SCHEDULER_DEBUG
	if (pb->GetNPackets() == 0)
		std::cout << "\t Send only reference symbols" << std::endl;
#endif

	GetMacEntity()->GetDevice()->SendPacketBurst(pb);
}

double DL_FLSEXP_PacketScheduler::ComputeSchedulingMetric(RadioBearer *bearer, double spectralEfficiency, int subChannel)
{
	double metric;
	switch (internalMetric)
	{
	case ENodeB::DLScheduler_EXP_RULE:
		metric = expRuleMetric(bearer, spectralEfficiency, subChannel, m_avgHOLDelayes);
		break;
	case ENodeB::DLScheduler_LOG_RULE:
		metric = logRuleMetric(bearer, spectralEfficiency);
		break;
	}
}

double pfMetric(RadioBearer *bearer, double spectralEfficiency){
	return (spectralEfficiency * 180000.) / bearer->GetAverageTransmissionRate();
}

double logRuleMetric(RadioBearer *bearer, double spectralEfficiency){
	double metric;

	if(bearer->GetApplication()->GetApplicationType() != Application::APPLICATION_TYPE_INFINITE_BUFFER){
		QoSParameters *qos = bearer->GetQoSParameters ();
		double HOL = bearer->GetHeadOfLinePacketDelay ();
		double targetDelay = qos->GetMaxDelay ();

		double logTerm = log (1.1 + ( (5 * HOL) / targetDelay ));
		double weight = (spectralEfficiency * 180000.) / bearer->GetAverageTransmissionRate();

		metric = logTerm * weight;
	}else{
		metric = pfMetric(bearer, spectralEfficiency);
	}
	return metric;
}

double expRuleMetric(RadioBearer *bearer, double spectralEfficiency, int subChannel, double m_avgHOLDelayes)
{
	double metric;

	if (bearer->GetApplication()->GetApplicationType() != Application::APPLICATION_TYPE_INFINITE_BUFFER)
	{
		QoSParameters *qos = bearer->GetQoSParameters();
		double HOL = bearer->GetHeadOfLinePacketDelay();
		double targetDelay = qos->GetMaxDelay();

		double numerator = (6 / targetDelay) * HOL;
		double denominator = (1 + sqrt(m_avgHOLDelayes));
		double weight = (spectralEfficiency * 180000.) / bearer->GetAverageTransmissionRate();
		metric = (exp(numerator / denominator)) * weight;
	}
	else
	{
		metric = pfMetric(bearer, spectralEfficiency);
	}
	return metric;
}

double DL_FLSEXP_PacketScheduler::ComputeAverageOfHOLDelays(void)
{
	double avgHOL = 0.;
	int nbFlows = 0;
	FlowsToSchedule *flowsToSchedule = GetFlowsToSchedule();
	FlowsToSchedule::iterator iter;
	FlowToSchedule *flow;

	for (iter = flowsToSchedule->begin(); iter != flowsToSchedule->end(); iter++)
	{
		flow = (*iter);
		if (flow->GetBearer()->HasPackets())
		{
			if (flow->GetBearer()->GetApplication()->GetApplicationType() != Application::APPLICATION_TYPE_INFINITE_BUFFER)
			{
				avgHOL += flow->GetBearer()->GetHeadOfLinePacketDelay();
				nbFlows++;
			}
		}
	}
	return avgHOL / nbFlows;
}

void DL_FLSEXP_PacketScheduler::RunControlLaw()
{
	m_runControlLaw = false;
	RrcEntity *rrc = GetMacEntity()->GetDevice()->GetProtocolStack()->GetRrcEntity();
	RrcEntity::RadioBearersContainer *bearers = rrc->GetRadioBearerContainer();

	for (std::vector<RadioBearer *>::iterator it = bearers->begin(); it != bearers->end(); it++)
	{
		RadioBearer *bearer = (*it);
		//Frame Level Scheduler Control Low!!!
		QoSForFLS *qos = (QoSForFLS *)bearer->GetQoSParameters();

		int queueSize = bearer->GetQueueSize();
		int *q = qos->GetQ();
		int *u = qos->GetU();
		double *c = qos->GetFilterCoefficients();
		int M = qos->GetNbOfCoefficients();

		double dataToTransmit = ((double)(1 - c[2]) * queueSize);
		for (int i = 0; i < M - 1; i++)
		{
			dataToTransmit += (double)q[i] * c[i + 2];
		}
		for (int i = 0; i < M - 2; i++)
		{
			dataToTransmit -= (double)q[i] * c[i + 3];
		}
		for (int i = 0; i < M - 1; i++)
		{
			dataToTransmit -= (double)u[i] * c[i + 2];
		}

		if (dataToTransmit < 0)
		{
			dataToTransmit = 0;
		}

		if (bearer->HasPackets())
		{
			int minData = 8 + bearer->GetHeadOfLinePacketSize();
			int maxData = bearer->GetMacQueue()->GetByte(dataToTransmit);
			if (dataToTransmit < minData)
			{
				dataToTransmit = minData;
			}
			else
			{
				if (dataToTransmit < maxData)
				{
					dataToTransmit = maxData;
				}
			}
		}
		qos->UpdateQ(queueSize);
		qos->UpdateU((ceil)(dataToTransmit));
		qos->SetDataToTransmit((ceil)(dataToTransmit));
	}
}

void DL_FLSEXP_PacketScheduler::Select_FlowsToSchedule()
{
	ClearFlowsToSchedule();

	RrcEntity *rrc = GetMacEntity()->GetDevice()->GetProtocolStack()->GetRrcEntity();
	RrcEntity::RadioBearersContainer *bearers = rrc->GetRadioBearerContainer();

	for (std::vector<RadioBearer *>::iterator it = bearers->begin(); it != bearers->end(); it++)
	{
		//SELECT FLOWS TO SCHEDULE
		RadioBearer *bearer = (*it);
		QoSForFLS *qos = (QoSForFLS *)bearer->GetQoSParameters();
		int dataToTransmit = NULL;

		if (bearer->HasPackets() && bearer->GetDestination()->GetNodeState() == NetworkNode::STATE_ACTIVE)
		{
			if (qos->GetDataToTransmit() > 0 && (bearer->GetApplication()->GetApplicationType() == Application::APPLICATION_TYPE_TRACE_BASED || bearer->GetApplication()->GetApplicationType() == Application::APPLICATION_TYPE_VOIP))
			{
				//data to transmit
				dataToTransmit = qos->GetDataToTransmit();
			}
			else if (bearer->GetApplication()->GetApplicationType() == Application::APPLICATION_TYPE_CBR || bearer->GetApplication()->GetApplicationType() == Application::APPLICATION_TYPE_INFINITE_BUFFER)
			{
				//compute data to transmit
				if (bearer->GetApplication()->GetApplicationType() == Application::APPLICATION_TYPE_INFINITE_BUFFER)
				{
					dataToTransmit = 100000;
				}
				else
				{
					dataToTransmit = bearer->GetQueueSize();
				}
			}
			//compute spectral efficiency
			ENodeB *enb = (ENodeB *)GetMacEntity()->GetDevice();
			ENodeB::UserEquipmentRecord *ueRecord = enb->GetUserEquipmentRecord(bearer->GetDestination()->GetIDNetworkNode());
			std::vector<double> spectralEfficiency;
			std::vector<int> cqiFeedbacks = ueRecord->GetCQI();
			int numberOfCqi = cqiFeedbacks.size();
			for (int i = 0; i < numberOfCqi; i++)
			{
				double sEff = GetMacEntity()->GetAmcModule()->GetEfficiencyFromCQI(cqiFeedbacks.at(i));
				spectralEfficiency.push_back(sEff);
			}
			//create flow to schedule record
			InsertFlowToSchedule(bearer, dataToTransmit, spectralEfficiency, cqiFeedbacks);
		}
	}
}

void DL_FLSEXP_PacketScheduler::UpdateDataToTransmitAndAverageDataRate(void)
{
	RrcEntity *rrc = GetMacEntity()->GetDevice()->GetProtocolStack()->GetRrcEntity();
	RrcEntity::RadioBearersContainer *bearers = rrc->GetRadioBearerContainer();

	for (std::vector<RadioBearer *>::iterator it = bearers->begin(); it != bearers->end(); it++)
	{
		RadioBearer *bearer = (*it);
		QoSForFLS *qos = (QoSForFLS *)bearer->GetQoSParameters();
		int dataToTransmit = qos->GetDataToTransmit();
		int transmittedData = bearer->GetTransmittedBytes();
		if (transmittedData >= dataToTransmit)
		{
			qos->SetDataToTransmit(0);
		}
		else
		{
			qos->SetDataToTransmit(dataToTransmit - transmittedData);
		}
		// UPDATE AVERAGE TRANSMISSION RATE
		bearer->UpdateAverageTransmissionRate();
	}
}
