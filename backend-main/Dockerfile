# ── Stage 1: 빌드 ──────────────────────────────────────────────────
FROM gradle:8-jdk17-alpine AS build
WORKDIR /app

# 의존성 캐시 레이어 (build.gradle만 먼저 복사)
COPY build.gradle settings.gradle ./
COPY gradle ./gradle
RUN gradle dependencies --no-daemon || true

# 소스 복사 후 빌드 (테스트 제외 - CI에서 이미 통과한 상태)
COPY src ./src
RUN gradle bootJar --no-daemon -x test

# ── Stage 2: 실행 ──────────────────────────────────────────────────
FROM eclipse-temurin:17-jre-alpine
WORKDIR /app

# 보안: root 대신 별도 유저로 실행
RUN addgroup -S spring && adduser -S spring -G spring
USER spring

COPY --from=build /app/build/libs/*.jar app.jar

EXPOSE 8080

ENTRYPOINT ["java", "-jar", "-Dspring.profiles.active=prod", "app.jar"]
