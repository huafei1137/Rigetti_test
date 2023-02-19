import qiskit

from qiskit import QuantumRegister, ClassicalRegister
from qiskit.providers.fake_provider import FakeMumbai, FakeCasablanca
from qiskit_rigetti import RigettiQCSProvider, QuilCircuit


def crosstalk_circuit(mylist):
    qregs = QuantumRegister(len(mylist), "q")
    # cregs = ClassicalRegister(len(mylist), 'c')
    qc = qiskit.QuantumCircuit(qregs)
    qc.x(mylist[0])
    qc.x(mylist[2])
    qc.barrier()
    qc.cx(mylist[0], mylist[1])
    qc.cx(mylist[2], mylist[3])
    qc.barrier()
    qc.measure_active()
    return qc


# def crosstalk_circuit_dd(mylist):
#     qregs = QuantumRegister(len(mylist), 'q')
#     cregs = ClassicalRegister(len(mylist), 'c')
#     qc = qiskit.QuantumCircuit(qregs,   cregs)
#     qc.x(mylist[0])
#     qc.x(mylist[2])
#     qc.barrier()
#     qc.cx(mylist[0],mylist[1])
#     qc.cx(mylist[2],mylist[3])
#     qc.barrier()
#     qc.measure_active()
#     return qc
def no_crosstalk_circuit(mylist):
    qregs = QuantumRegister(len(mylist), "q")
    # cregs = ClassicalRegister(len(mylist), 'c')
    qc = qiskit.QuantumCircuit(qregs)
    qc.x(mylist[0])
    qc.x(mylist[2])

    qc.cx(mylist[0], mylist[1])
    qc.barrier()
    qc.cx(mylist[2], mylist[3])
    qc.barrier()
    qc.measure_active()
    return qc


from qiskit.transpiler import CouplingMap
import random


def generate_random_crosstalk_pair(backend):
    cg = backend.configuration()
    cm = cg.to_dict()["coupling_map"]
    cm = CouplingMap(cm)
    config = backend.configuration()

    res_list = []
    temp_list = []
    for i1 in range(0, config.n_qubits - 1):
        for i2 in range(0, config.n_qubits - 1):
            for i3 in range(0, config.n_qubits - 1):
                for i4 in range(0, config.n_qubits - 1):
                    if (
                        i1 != i2
                        and i1 != i3
                        and i1 != i4
                        and i2 != i3
                        and i2 != i4
                        and i4 != i3
                    ):
                        if (
                            CouplingMap.distance(cm, i1, i2) == 1
                            and CouplingMap.distance(cm, i2, i3) == 1
                            and CouplingMap.distance(cm, i3, i4) == 1
                        ):
                            res_list.append([i1, i2, i3, i4])

    return res_list


def run_program(backend, shots):
    mylist = [0, 1, 2, 3]
    save_index = {}
    res_base = {}
    res_our = {}

    for i, physical in enumerate(generate_random_crosstalk_pair(backend)):
        # physical = generate_random_crosstalk_pair(backend)
        qc_c = crosstalk_circuit(mylist)
        qc_n = no_crosstalk_circuit(mylist)
        # qc_c_c = qiskit.transpile(
        #     qc_c, backend=backend, initial_layout=physical, scheduling_method="asap"
        # )
        # qc_n_c = qiskit.transpile(
        #     qc_n, backend=backend, initial_layout=physical, scheduling_method="asap"
        # )
        # pm = PassManager([ALAPSchedule(dt),
        #           DynamicalDecoupling(dt, dd_sequence)])
        # circ_dd = pm.run(qc_c)
        # qc_c_dd = qiskit.transpile(circ_dd,backend=backend,scheduling_method='asap')
        # qc_c_c.draw(output='mpl')
        print(f'{physical} qubit pair sent to the job')
        save_index[i] = physical
        job_result_crosstalk = backend.run(qc_c, shots=shots)
        job_result_no = backend.run(qc_n, shots=shots)
        # job_result_dd = backend.run(qc_c_dd,shots=shots)
        res_base[i] = job_result_crosstalk
        res_our[i] = job_result_no
        # res_dd[i] = job_result_dd
    # print(qc_c_c)
    # print(qc_n_c)
    print(f"all jobs have been sent to machines")
    # job_result_crosstalk = backend.run(qc_c_c,shots=shots)
    # job_result_no = backend.run(qc_n_c,shots=shots)
    # res.append(job_result_crosstalk)
    # res.append(job_result_no)
    return save_index, res_our, res_base


def evaluate(save_index, res_crosstalk_our, res_crosstalk_base, shots):

    for i in range(len(save_index)):
        error_p1_i = get_fidelity(res_crosstalk_our[i].result().get_counts(), shots, 0)
        error_p2_i = get_fidelity(res_crosstalk_our[i].result().get_counts(), shots, 1)
        error_p1_c = get_fidelity(res_crosstalk_base[i].result().get_counts(), shots, 0)
        error_p2_c = get_fidelity(res_crosstalk_base[i].result().get_counts(), shots, 0)
        # diff = res_crosstalk_our[i].result().get_counts()['1111'] - res_crosstalk_base[i].result().get_counts()['1111']
        # diff = diff/8000
        print(
            f"we pick {save_index[i]}, simutaneously the first piar of qubit error is {error_p1_i}, the second pair is {error_p2_i}, with raito {error_p1_i/error_p1_c} and {error_p2_i/error_p2_c} "
        )


def get_fidelity(r, shots, flag):
    counts = 0
    if flag == 0:
        for state in r:
            if state.startswith("11"):
                counts += r[state]
        return 1 - counts / shots
    else:
        for state in r:
            if state.endswith("11"):
                counts += r[state]
        return 1 - counts / shots


def main():

    backend = FakeCasablanca()
    # Get provider and backend

    # p = RigettiQCSProvider()
    # backend = p.get_simulator(num_qubits=2, noisy=True)  # or p.get_backend(name='Aspen-9')

    shots = 8000
    rr = generate_random_crosstalk_pair(backend)
    print(f"all the crosstalk test pair are:")
    print(rr)

    save_index, res_crosstalk_our, res_crosstalk_base = run_program(backend, shots)
    evaluate(save_index, res_crosstalk_our, res_crosstalk_base, shots)


if __name__ == "__main__":
    main()
