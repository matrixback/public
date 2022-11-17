## 搜索某一个 studio 的课程

url: path('studio/<int:pk>/class_schedule/', ClassScheduleListView.as_view())

```
class ClassScheduleListView(generics.ListAPIView):
    """
    As a user, I want to search/filter a studio's class schedule. 
    The search/filter can be based on the class name, coach name, date, and time range.
    """
    authentication_classes = [BearerTokenAuthentication]
    permission_classes = [IsAuthenticated]
    serializer_class = ClassScheduleSerializer
    queryset = Studio.objects.all()

    def list(self, request, *args, **kwargs):
        studio = self.get_object() # 首先，根据 pk(primary key) 拿到 对应的 studio
        classes = studio.classes.all() # 获取到所有的 classes
        # 根据请求的 params 进行查询
        # 如果有 name，就搜索包含有此 name 的 class
        name = self.request.query_params.get('name') 
        if name is not None:
            classes = classes.filter(name__contains=name)

        coach = self.request.query_params.get('coach')
        if coach is not None:
            classes = classes.filter(coach__contains=coach)

        start_time = self.request.query_params.get('start_time')
        end_time = self.request.query_params.get('end_time')
        if start_time and end_time:
            start_time = datetime.strptime(start_time, '%H:%M:%S')
            end_time = datetime.strptime(end_time, '%H:%M:%S')
            classes = classes.filter(start_time__lte=start_time)
            classes = classes.filter(end_time__gte=end_time)

        rv = []
        for class_ in classes:
            # 获取到这些课程的课程表
            schedules = class_.schedules.all()
            # 再次通过 date 搜索过滤
            date = self.request.query_params.get('date')
            if date is not None:
                date = datetime.strptime(date, "%Y-%m-%d")
                schedules = schedules.filter(date=date).filter(is_active=True).all()
            else:
                today = datetime.now()
                schedules = schedules.filter(date__gte=today).filter(is_active=True).all()

            rv.extend(ClassScheduleSerializer(schedules, many=True).data)
        # 根据日期再排序
        rv.sort(key=cmp_to_key(self.schedule_cmp))
        
        return Response(rv)
```
