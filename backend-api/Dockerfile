# P1 — Spring Boot application backend. Build context: backend-api/ (this
# directory) — the module is fully self-contained, unlike the Python
# services, which need sibling packages from the repo root.
#
# Java 25, not 21: pom.xml pins <java.version>25</java.version>. A JDK 21
# image fails here with "release version 25 not supported" — caught by
# actually building this image, not just assuming a version.
FROM maven:3.9-eclipse-temurin-25 AS build
WORKDIR /app
COPY pom.xml .
RUN mvn -B dependency:go-offline
COPY src src
RUN mvn -B clean package -DskipTests

FROM eclipse-temurin:25-jre
WORKDIR /app
COPY --from=build /app/target/backend-api-*.jar app.jar
EXPOSE 8080
ENTRYPOINT ["java", "-jar", "app.jar"]
