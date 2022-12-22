FROM php:7.4-fpm-alpine
RUN apk add --no-cache libzip-dev zip
RUN docker-php-ext-install zip
