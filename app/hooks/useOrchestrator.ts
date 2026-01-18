/**
 * useOrchestrator Hook
 *
 * 提供前端与 Orchestrator 交互的接口
 * 前端通过发送事件来驱动状态变化，从不直接决定下一步做什么
 */

import { useState, useCallback, useEffect, useRef } from "react";
import {
  OrchestratorState,
  OrchestratorEvent,
  ORCHESTRATOR_EVENTS,
  Task,
  TimeBoxRecommendation,
} from "../types";
import { orchestrator, initialOrchestratorState } from "../orchestrator";

export interface UseOrchestratorReturn {
  // 状态
  state: OrchestratorState;
  recommendation: TimeBoxRecommendation | null;
  isLoadingRecommendation: boolean;
  hasActiveTimeBox: boolean;

  // 事件发送器
  events: {
    appStart: (tasks: Task[]) => Promise<void>;
    timeBoxStarted: (taskId: string, durationMinutes: number) => Promise<void>;
    timeBoxEnded: (
      taskId: string,
      durationMinutes: number,
      actualMinutes: number
    ) => Promise<void>;
    timeBoxInterrupted: (
      taskId: string,
      durationMinutes: number,
      elapsedMinutes: number,
      reason?: string
    ) => Promise<void>;
    requestNew: (preferLowCognitiveLoad?: boolean) => Promise<void>;
  };

  // 工具函数
  updateTasks: (tasks: Task[]) => void;
  acceptRecommendation: () => { taskId: string; durationMinutes: number } | null;
}

export const useOrchestrator = (): UseOrchestratorReturn => {
  const [state, setState] = useState<OrchestratorState>(initialOrchestratorState);
  const isInitialized = useRef(false);

  /**
   * 发送事件到 Orchestrator
   */
  const sendEvent = useCallback(async (event: OrchestratorEvent) => {
    const result = await orchestrator.handleEvent(event);
    setState(result.newState);
  }, []);

  /**
   * APP_START 事件
   */
  const appStart = useCallback(
    async (tasks: Task[]) => {
      await sendEvent({
        event: ORCHESTRATOR_EVENTS.APP_START,
        payload: { tasks },
        state,
      });
    },
    [sendEvent, state]
  );

  /**
   * TIMEBOX_STARTED 事件
   */
  const timeBoxStarted = useCallback(
    async (taskId: string, durationMinutes: number) => {
      await sendEvent({
        event: ORCHESTRATOR_EVENTS.TIMEBOX_STARTED,
        payload: { taskId, durationMinutes },
        state,
      });
    },
    [sendEvent, state]
  );

  /**
   * TIMEBOX_ENDED 事件
   */
  const timeBoxEnded = useCallback(
    async (
      taskId: string,
      durationMinutes: number,
      actualMinutes: number
    ) => {
      await sendEvent({
        event: ORCHESTRATOR_EVENTS.TIMEBOX_ENDED,
        payload: { taskId, durationMinutes, actualMinutes },
        state,
      });
    },
    [sendEvent, state]
  );

  /**
   * TIMEBOX_INTERRUPTED 事件
   */
  const timeBoxInterrupted = useCallback(
    async (
      taskId: string,
      durationMinutes: number,
      elapsedMinutes: number,
      reason?: string
    ) => {
      await sendEvent({
        event: ORCHESTRATOR_EVENTS.TIMEBOX_INTERRUPTED,
        payload: { taskId, durationMinutes, elapsedMinutes, reason },
        state,
      });
    },
    [sendEvent, state]
  );

  /**
   * REQUEST_NEW 事件
   */
  const requestNew = useCallback(
    async (preferLowCognitiveLoad?: boolean) => {
      await sendEvent({
        event: ORCHESTRATOR_EVENTS.REQUEST_NEW,
        payload: { preferLowCognitiveLoad },
        state,
      });
    },
    [sendEvent, state]
  );

  /**
   * 更新任务池（不触发推荐）
   */
  const updateTasks = useCallback((tasks: Task[]) => {
    setState((prevState) => orchestrator.updateTasks(prevState, tasks));
  }, []);

  /**
   * 接受当前推荐（返回推荐内容供前端使用）
   */
  const acceptRecommendation = useCallback(() => {
    if (!state.recommendation) {
      return null;
    }
    return {
      taskId: state.recommendation.taskId,
      durationMinutes: state.recommendation.durationMinutes,
    };
  }, [state.recommendation]);

  return {
    // 状态
    state,
    recommendation: state.recommendation,
    isLoadingRecommendation: state.isLoadingRecommendation,
    hasActiveTimeBox: state.activeTimeBox !== null,

    // 事件发送器
    events: {
      appStart,
      timeBoxStarted,
      timeBoxEnded,
      timeBoxInterrupted,
      requestNew,
    },

    // 工具函数
    updateTasks,
    acceptRecommendation,
  };
};
