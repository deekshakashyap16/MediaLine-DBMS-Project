-- Unified MySQL script for database `medialine`
-- Target MySQL version: 8.0.43
-- Contains: CREATE TABLE, INSERT, TRIGGERS, PROCEDURES, FUNCTIONS, VIEWS
-- Drop and recreate objects to ensure a single-file import

-- Session safety settings
/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!50503 SET NAMES utf8mb4 */;
/*!40103 SET @OLD_TIME_ZONE=@@TIME_ZONE */;
/*!40103 SET TIME_ZONE='+00:00' */;
/*!40014 SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0 */;
/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;
/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;
/*!40111 SET @OLD_SQL_NOTES=@@SQL_NOTES, SQL_NOTES=0 */;

CREATE DATABASE IF NOT EXISTS `media_line` DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci;
USE `media_line`;

-- -------------------------------------------------------------------------
-- Tables (order chosen to satisfy foreign key dependencies)
-- -------------------------------------------------------------------------

-- content
DROP TABLE IF EXISTS `content`;
CREATE TABLE `content` (
  `Media_ID` int NOT NULL,
  `Name` varchar(255) NOT NULL,
  `Type` varchar(50) NOT NULL,
  `Descr` text NOT NULL,
  `Age_rating` varchar(10) NOT NULL,
  `Ratings` float DEFAULT NULL,
  `Release_date` date NOT NULL,
  `Num_of_streams` int NOT NULL,
  `Language` varchar(50) NOT NULL,
  PRIMARY KEY (`Media_ID`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- user
DROP TABLE IF EXISTS `user`;
CREATE TABLE `user` (
  `User_ID` int NOT NULL,
  `Username` varchar(255) NOT NULL,
  `Password` varchar(255) NOT NULL,
  `Name` varchar(255) NOT NULL,
  `DOB` date NOT NULL,
  `Address` varchar(255) NOT NULL,
  `Email` varchar(255) NOT NULL,
  `Credit_card_info` varchar(255) NOT NULL,
  `Phone` varchar(50) NOT NULL,
  `Sub_start_date` date NOT NULL,
  PRIMARY KEY (`User_ID`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- movie
DROP TABLE IF EXISTS `movie`;
CREATE TABLE `movie` (
  `Media_ID` int NOT NULL,
  `Total_duration` int DEFAULT NULL,
  `Movie_File` longblob,
  PRIMARY KEY (`Media_ID`),
  CONSTRAINT `movie_ibfk_1` FOREIGN KEY (`Media_ID`) REFERENCES `content` (`Media_ID`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- series
DROP TABLE IF EXISTS `series`;
CREATE TABLE `series` (
  `Media_ID` int NOT NULL,
  `num_of_seasons` int NOT NULL,
  `num_of_episodes` int NOT NULL,
  PRIMARY KEY (`Media_ID`),
  CONSTRAINT `series_ibfk_1` FOREIGN KEY (`Media_ID`) REFERENCES `content` (`Media_ID`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- episode (references series)
DROP TABLE IF EXISTS `episode`;
CREATE TABLE `episode` (
  `Episode_ID` int NOT NULL,
  `Season_number` int NOT NULL,
  `Episode_number` int NOT NULL,
  `Episode_name` varchar(255) NOT NULL,
  `Duration` int NOT NULL,
  `Air_date` date NOT NULL,
  `Media_ID` int NOT NULL,
  `Episode_File` longblob,
  PRIMARY KEY (`Episode_ID`),
  KEY `Media_ID` (`Media_ID`),
  CONSTRAINT `episode_ibfk_1` FOREIGN KEY (`Media_ID`) REFERENCES `series` (`Media_ID`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- genre
DROP TABLE IF EXISTS `genre`;
CREATE TABLE `genre` (
  `Media_ID` int NOT NULL,
  `Genre_name` varchar(100) NOT NULL,
  PRIMARY KEY (`Media_ID`,`Genre_name`),
  CONSTRAINT `genre_ibfk_1` FOREIGN KEY (`Media_ID`) REFERENCES `content` (`Media_ID`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- team
DROP TABLE IF EXISTS `team`;
CREATE TABLE `team` (
  `Member_ID` int NOT NULL,
  `Member_name` varchar(255) NOT NULL,
  `Role` varchar(100) DEFAULT NULL,
  `Media_ID` int NOT NULL,
  PRIMARY KEY (`Member_ID`),
  KEY `Media_ID` (`Media_ID`),
  CONSTRAINT `team_ibfk_1` FOREIGN KEY (`Media_ID`) REFERENCES `content` (`Media_ID`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- team_assignment
DROP TABLE IF EXISTS `team_assignment`;
CREATE TABLE `team_assignment` (
  `Member_ID` int NOT NULL,
  `Media_ID` int NOT NULL,
  PRIMARY KEY (`Member_ID`,`Media_ID`),
  KEY `Media_ID` (`Media_ID`),
  CONSTRAINT `team_assignment_ibfk_1` FOREIGN KEY (`Member_ID`) REFERENCES `team` (`Member_ID`),
  CONSTRAINT `team_assignment_ibfk_2` FOREIGN KEY (`Media_ID`) REFERENCES `content` (`Media_ID`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- trailer
DROP TABLE IF EXISTS `trailer`;
CREATE TABLE `trailer` (
  `Media_ID` int NOT NULL,
  `Trailer_name` varchar(255) NOT NULL,
  `Trailer_duration` int DEFAULT NULL,
  PRIMARY KEY (`Media_ID`,`Trailer_name`),
  CONSTRAINT `trailer_ibfk_1` FOREIGN KEY (`Media_ID`) REFERENCES `content` (`Media_ID`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- curr_watch (references user and content)
DROP TABLE IF EXISTS `curr_watch`;
CREATE TABLE `curr_watch` (
  `User_ID` int NOT NULL,
  `Media_ID` int NOT NULL,
  `Date_watched` date NOT NULL,
  `Duration_watched` int NOT NULL,
  PRIMARY KEY (`User_ID`,`Media_ID`,`Date_watched`),
  KEY `Media_ID` (`Media_ID`),
  CONSTRAINT `curr_watch_ibfk_1` FOREIGN KEY (`User_ID`) REFERENCES `user` (`User_ID`),
  CONSTRAINT `curr_watch_ibfk_2` FOREIGN KEY (`Media_ID`) REFERENCES `content` (`Media_ID`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- download (references user and content)
DROP TABLE IF EXISTS `download`;
CREATE TABLE `download` (
  `User_ID` int NOT NULL,
  `Media_ID` int NOT NULL,
  `Download_Date` date NOT NULL,
  PRIMARY KEY (`User_ID`,`Media_ID`),
  KEY `Media_ID` (`Media_ID`),
  CONSTRAINT `download_ibfk_1` FOREIGN KEY (`User_ID`) REFERENCES `user` (`User_ID`),
  CONSTRAINT `download_ibfk_2` FOREIGN KEY (`Media_ID`) REFERENCES `content` (`Media_ID`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- liked (references user and content)
DROP TABLE IF EXISTS `liked`;
CREATE TABLE `liked` (
  `User_ID` int NOT NULL,
  `Media_ID` int NOT NULL,
  `date_liked` date DEFAULT NULL,
  PRIMARY KEY (`User_ID`,`Media_ID`),
  KEY `Media_ID` (`Media_ID`),
  CONSTRAINT `liked_ibfk_1` FOREIGN KEY (`User_ID`) REFERENCES `user` (`User_ID`),
  CONSTRAINT `liked_ibfk_2` FOREIGN KEY (`Media_ID`) REFERENCES `content` (`Media_ID`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- -------------------------------------------------------------------------
-- Data inserts
-- -------------------------------------------------------------------------

-- content rows
INSERT INTO `content` (`Media_ID`,`Name`,`Type`,`Descr`,`Age_rating`,`Ratings`,`Release_date`,`Num_of_streams`,`Language`) VALUES
(1,'Michelle Obama: The Story','Movie','A deep dive into the inspiring journey of Michelle Obama.','PG',8.7,'2020-10-15',12000,'English'),
(2,'The Diana Story Part III: Legacy of Love','Movie','The untold legacy of Princess Diana and her impact on modern history.','PG-13',9.1,'2021-07-22',9500,'English'),
(3,'Saturday Night Live','Series','Comedy sketches, satire, and live music — Season 49 & 50.','PG-13',8.9,'2024-01-10',50000,'English'),
(4,'Hero X','Series','A Chinese sci-fi series exploring the lives of 10 superheroes as their destinies intertwine.','R',9.2,'2023-09-05',42000,'Mandarin');

-- user rows
INSERT INTO `user` (`User_ID`,`Username`,`Password`,`Name`,`DOB`,`Address`,`Email`,`Credit_card_info`,`Phone`,`Sub_start_date`) VALUES
(1,'deeksha_k','pass123','Deeksha','2003-05-14','Bangalore','deeksha@example.com','1234-5678-9012-3456','9876543210','2025-01-10'),
(2,'darshana_v','pass234','Darshana','2002-11-22','Mysore','darshana@example.com','5678-9012-3456-7890','8765432109','2025-02-01'),
(3,'sankalp_r','pass345','Sankalp','2003-08-09','Chennai','sankalp@example.com','9012-3456-7890-1234','7654321098','2025-03-15');

-- movie rows
INSERT INTO `movie` (`Media_ID`,`Total_duration`,`Movie_File`) VALUES
(1,7200,NULL),
(2,6800,NULL);

-- series rows
INSERT INTO `series` (`Media_ID`,`num_of_seasons`,`num_of_episodes`) VALUES
(3,2,10),
(4,1,2);

-- episode rows
INSERT INTO `episode` (`Episode_ID`,`Season_number`,`Episode_number`,`Episode_name`,`Duration`,`Air_date`,`Media_ID`,`Episode_File`) VALUES
(1,50,2,'Weekend Update: Season 50 Episode 2',1800,'2025-02-01',3,NULL),
(2,49,5,'Celebrity Cold Opens: Season 49 Episode 5',1750,'2024-09-15',3,NULL),
(3,1,1,'Nice',2400,'2023-09-05',4,NULL),
(4,1,2,'Moon',2500,'2023-09-12',4,NULL);

-- genre rows
INSERT INTO `genre` (`Media_ID`,`Genre_name`) VALUES
(1,'Biography'),
(1,'Inspirational'),
(2,'Documentary'),
(2,'History'),
(3,'Comedy'),
(3,'Variety Show'),
(4,'Action'),
(4,'Sci-Fi');

-- team rows
INSERT INTO `team` (`Member_ID`,`Member_name`,`Role`,`Media_ID`) VALUES
(1,'Ava Reynolds','Director',1),
(2,'Michelle Obama','Actor',1),
(3,'Daniel Craig','Actor',1),
(4,'Thomas Blake','Director',2),
(5,'Emma Thompson','Actor',2),
(6,'Olivia Colman','Actor',2),
(7,'Lorne Michaels','Director',3),
(8,'Kenan Thompson','Actor',3),
(9,'Chloe Fineman','Actor',3),
(10,'Wei Zhang','Director',4),
(11,'Li Na','Actor',4),
(12,'Chen Hao','Actor',4);

-- team_assignment rows
INSERT INTO `team_assignment` (`Member_ID`,`Media_ID`) VALUES
(1,1),(2,1),(3,1),(4,2),(5,2),(6,2),(7,3),(8,3),(9,3),(10,4),(11,4),(12,4);

-- trailer rows
INSERT INTO `trailer` (`Media_ID`,`Trailer_name`,`Trailer_duration`) VALUES
(3,'SNL Season 50 Official Trailer',150),
(4,'Hero X Official Trailer',180);

-- curr_watch rows
-- NOTE: PRIMARY KEY on curr_watch includes Date_watched to allow multiple days per user-media pair
INSERT INTO `curr_watch` (`User_ID`,`Media_ID`,`Date_watched`,`Duration_watched`) VALUES
(1,1,'2025-11-05',2400),
(1,4,'2025-11-04',1800),
(2,3,'2025-11-03',1500),
(2,4,'2025-11-04',2000),
(3,1,'2025-11-01',2700),
(3,2,'2025-11-02',2500);

-- liked rows
INSERT INTO `liked` (`User_ID`,`Media_ID`,`date_liked`) VALUES
(1,2,'2025-11-04'),
(2,3,'2025-11-05');

-- download has no initial rows in the dump

-- -------------------------------------------------------------------------
-- Triggers
-- -------------------------------------------------------------------------
DELIMITER $$

-- default crew role for team
CREATE TRIGGER `trg_default_crew_role`
BEFORE INSERT ON `team`
FOR EACH ROW
BEGIN
    SET NEW.Role = IF(NEW.Role IS NULL, 'Crew', NEW.Role);
END $$

-- clip watch duration protection: if watched duration > movie total, set to 0
CREATE TRIGGER `trg_clip_watch_duration`
BEFORE INSERT ON `curr_watch`
FOR EACH ROW
BEGIN
    DECLARE total_duration INT;
    SELECT Total_duration INTO total_duration FROM movie WHERE Media_ID = NEW.Media_ID;

    IF total_duration IS NOT NULL AND NEW.Duration_watched > total_duration THEN
        SET NEW.Duration_watched = 0;
    END IF;
END $$

-- default download date
CREATE TRIGGER `trg_download_default_date`
BEFORE INSERT ON `download`
FOR EACH ROW
BEGIN
    SET NEW.Download_Date = IFNULL(NEW.Download_Date, CURDATE());
END $$

-- prevent duplicate likes
CREATE TRIGGER `trg_prevent_duplicate_like`
BEFORE INSERT ON `liked`
FOR EACH ROW
BEGIN
    IF EXISTS (
        SELECT 1 FROM liked 
        WHERE User_ID = NEW.User_ID AND Media_ID = NEW.Media_ID
    ) THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'User already liked this content';
    END IF;
END $$

-- increment num_of_streams after insert into curr_watch
CREATE TRIGGER `trg_increment_streams`
AFTER INSERT ON `curr_watch`
FOR EACH ROW
BEGIN
    UPDATE content
    SET Num_of_streams = Num_of_streams + 1
    WHERE Media_ID = NEW.Media_ID;
END $$

DELIMITER ;

-- -------------------------------------------------------------------------
-- Stored Procedures
-- -------------------------------------------------------------------------
DELIMITER $$

CREATE PROCEDURE `sp_watch_now`(IN u_id INT, IN m_id INT, IN duration INT)
BEGIN
    DECLARE existing_duration INT;

    SELECT Duration_watched INTO existing_duration
    FROM curr_watch
    WHERE User_ID = u_id AND Media_ID = m_id AND Date_watched = CURDATE()
    LIMIT 1;

    IF existing_duration IS NOT NULL THEN
        UPDATE curr_watch
        SET Duration_watched = Duration_watched + duration
        WHERE User_ID = u_id AND Media_ID = m_id AND Date_watched = CURDATE();
    ELSE
        INSERT INTO curr_watch (User_ID, Media_ID, Date_watched, Duration_watched)
        VALUES (u_id, m_id, CURDATE(), duration);
    END IF;
END $$

CREATE PROCEDURE `sp_like_content`(IN u_id INT, IN m_id INT)
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM liked WHERE User_ID = u_id AND Media_ID = m_id
    ) THEN
        INSERT INTO liked (User_ID, Media_ID, date_liked)
        VALUES (u_id, m_id, CURDATE());
    END IF;
END $$

CREATE PROCEDURE `sp_add_user`(
    IN uname VARCHAR(255), IN pwd VARCHAR(255), IN name_in VARCHAR(255),
    IN dob DATE, IN addr VARCHAR(255), IN email VARCHAR(255),
    IN card VARCHAR(255), IN phone VARCHAR(50), IN start_date DATE
)
BEGIN
    INSERT INTO `user` (Username, Password, Name, DOB, Address, Email, Credit_card_info, Phone, Sub_start_date)
    VALUES (uname, pwd, name_in, dob, addr, email, card, phone, start_date);
END $$

CREATE PROCEDURE `sp_top_movies`(IN n INT)
BEGIN
    SELECT Name, Num_of_streams
    FROM content
    WHERE Type='Movie'
    ORDER BY Num_of_streams DESC
    LIMIT n;
END $$

CREATE PROCEDURE `sp_watch_history`(IN u_id INT)
BEGIN
    SELECT c.Name, cw.Date_watched, cw.Duration_watched
    FROM curr_watch cw
    JOIN content c ON cw.Media_ID = c.Media_ID
    WHERE cw.User_ID = u_id;
END $$

DELIMITER ;

-- -------------------------------------------------------------------------
-- Views
-- -------------------------------------------------------------------------

CREATE OR REPLACE VIEW `vw_popular_content` AS
SELECT Media_ID, Name, Type, Num_of_streams
FROM content
ORDER BY Num_of_streams DESC
LIMIT 10;

CREATE OR REPLACE VIEW `vw_user_watch_summary` AS
SELECT u.User_ID, u.Name, COUNT(cw.Media_ID) AS Total_Watched, IFNULL(SUM(cw.Duration_watched),0) AS Total_Duration
FROM `user` u
LEFT JOIN curr_watch cw ON u.User_ID = cw.User_ID
GROUP BY u.User_ID;

CREATE OR REPLACE VIEW `vw_movie_cast` AS
SELECT m.Media_ID, m.Media_ID AS MediaID_check, t.Member_name AS Crew_Member, t.Role
FROM movie m
JOIN team t ON m.Media_ID = t.Media_ID;

CREATE OR REPLACE VIEW `vw_user_likes` AS
SELECT u.User_ID, u.Name, c.Name AS Content_Name, c.Type
FROM liked l
JOIN `user` u ON l.User_ID = u.User_ID
JOIN content c ON l.Media_ID = c.Media_ID;

-- -------------------------------------------------------------------------
-- Functions
-- -------------------------------------------------------------------------
DELIMITER $$

CREATE FUNCTION `fn_total_watch_time`(u_id INT)
RETURNS INT
DETERMINISTIC
BEGIN
    DECLARE total_time INT;
    SELECT SUM(Duration_watched) INTO total_time
    FROM curr_watch
    WHERE User_ID = u_id;
    RETURN IFNULL(total_time, 0);
END $$

CREATE FUNCTION `fn_has_watched`(u_id INT, m_id INT)
RETURNS BOOLEAN
DETERMINISTIC
BEGIN
    DECLARE cnt INT;
    SELECT COUNT(*) INTO cnt
    FROM curr_watch
    WHERE User_ID = u_id AND Media_ID = m_id;
    RETURN cnt > 0;
END $$

CREATE FUNCTION `fn_total_viewers`(m_id INT)
RETURNS INT
DETERMINISTIC
BEGIN
    DECLARE viewer_count INT;
    SELECT COUNT(DISTINCT User_ID) INTO viewer_count
    FROM curr_watch
    WHERE Media_ID = m_id;
    RETURN IFNULL(viewer_count, 0);
END $$

CREATE FUNCTION `fn_episode_count`(m_id INT)
RETURNS INT
DETERMINISTIC
BEGIN
    DECLARE ep_count INT;
    SELECT COUNT(*) INTO ep_count
    FROM episode
    WHERE Media_ID = m_id;
    RETURN IFNULL(ep_count, 0);
END $$

DELIMITER ;

-- -------------------------------------------------------------------------
-- Final session restore
-- -------------------------------------------------------------------------
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;
/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;

-- End of unified script
