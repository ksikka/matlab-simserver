% A discrete time simulation shell.
classdef SimWrapper < handle
    properties
        time
        results
    end

    methods
        function [obj] = SimWrapper()
            obj.time = 0;
            obj.stepTo(1);
        end

        function [] = step(obj)
            obj.time = obj.time + 1;
        end

        function [] = stepTo(obj, T)
            if (T < 1)
                return
            end
            if (T < obj.time)
                msg = strcat('You tried to go from ', num2str(obj.time), ' to ', num2str(T));
                throw(MException('SimWrapper:BackInTime',msg));
            end
        end

        function [results] = getState(obj)
            results = obj.results(obj.time,:);
        end

        function [results] = getResultsAt(obj, T)
            obj.stepTo(T);
            results = obj.results(T,:);
        end
    end
end

