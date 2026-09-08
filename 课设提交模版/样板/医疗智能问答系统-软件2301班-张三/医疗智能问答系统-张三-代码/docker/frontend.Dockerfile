FROM node:18-alpine AS builder
WORKDIR /app
COPY frontend/package*.json ./
RUN npm config set registry http://mirrors.cloud.tencent.com/npm/ && npm install
COPY frontend/ .
RUN npm run build

FROM nginx:alpine
COPY docker/nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=builder /app/dist /usr/share/nginx/html
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
