CREATE DATABASE `safegridai` /*!40100 DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci */ /*!80016 DEFAULT ENCRYPTION='N' */;
CREATE TABLE `camera` (
  `id` int NOT NULL,
  `stream_ip` varchar(45) NOT NULL,
  `location` varchar(200) NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
CREATE TABLE `detection_log` (
  `id` int NOT NULL AUTO_INCREMENT,
  `mask_flag` tinyint NOT NULL,
  `image` varchar(200) NOT NULL,
  `camera_id` int NOT NULL,
  `timestamp` datetime NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
CREATE TABLE `recognition_log` (
  `id` int NOT NULL AUTO_INCREMENT,
  `suspect_id` int NOT NULL,
  `detection_id` int NOT NULL,
  `confidance` float NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
CREATE TABLE `suspect` (
  `id` int NOT NULL AUTO_INCREMENT,
  `serial` varchar(10) NOT NULL,
  `name` varchar(45) NOT NULL DEFAULT 'unknown',
  `image` varchar(200) NOT NULL,
  `embed` blob NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
CREATE TABLE `user` (
  `id` int NOT NULL AUTO_INCREMENT,
  `username` varchar(45) NOT NULL,
  `password` varchar(45) NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
