
一个应用 (Application)由一个Driver和若干个Job构成，

一个Job由多个阶段(Stage)构成，

一个阶段(Stage)由多个任务 (Task)组成。

当执行一个应用时，任务控制节点Driver会向集群管理器 (Cluster Manager)申请资源，启动
Executor， 并向Executor发送应用程序代码和文件，然后在Executor上执行任务，运行结束后，执行结果会返回给任务控制节点Driver，写到HDFS或者其他数据库中。



Spark Core:Spark Core包含Spark最基础和最核心的功能，如内存计算、任务调度、部署模式、故障恢复、存储管理等，主要面向批数据处理。Spark Core建立在统一的抽象RDD之上，使其可以以基本一致的方式应对不同的大数据处理场景；需要注意的是，Spark Core通常被简称为Spark。

Spark SQL:Spark saL-是用于结构化数据处理的组件，允许开发人员直接处理RDD，同时也可查询Hive、HBase等外部数据源。Spark sQL的一个重要特点是其能够统一处理关系表和RDD，使得开发人员不需要自己编写Spark应用程序，开发人员可以轻松地使用SQL命令进行查询，并进行更复杂的数据分析。

Spark Streaming:Spark Streaming是一种流计算框架，可以支持高吞吐量、可容错处理的实时流数据处理，其核心思路是将流数据分解成一系列短小的批处理作业，每个短小的批处理作业都可以使用Spark Core进行快速处理。Spark Streaming支持多种数据输入源，如Kafka、Flume 和TCP套接字等。

MLlib （机器学习）MLlib提供了常用机器学习算法的实现，包括聚类、分类、回归、协同过滤等，降低了机器学习的门槛，开发人员只要具备一定的理论知识就能进行机器学习方面的工作。

Graphx （图计算）：Graphx是Spark中用于图计算的APl，可认为是Pregel在Spark上的重写及优化，Graphx性能良好，拥有丰富的功能和运算符，能在海量数据上自如地运行复杂的图算法。